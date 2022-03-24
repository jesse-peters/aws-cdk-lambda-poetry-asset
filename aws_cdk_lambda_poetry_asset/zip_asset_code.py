import glob
import logging
import os
import platform
import shutil
import uuid
from pathlib import Path
from typing import List

import docker
import requests
from aws_cdk.aws_lambda import AssetCode

BUILD_IMAGE = "python:3.9.11-bullseye"


def is_linux() -> bool:
    """
    :return: True if running on Linux. False otherwise.
    """
    return platform.system().lower() == "linux"


class ZipAssetCode(AssetCode):
    """
    CDK AssetCode which builds lambda function and produces a ZIP file with dependencies.
    Lambda function is built either in Docker or natively when running on Linux.
    """

    def __init__(
        self,
        include: List[str],
        work_dir: Path,
        file_name: str = str(uuid.uuid4())[:8],
        create_file_if_exists: bool = True,
        use_docker_non_linux: bool = True,
    ) -> None:
        """
        :param include: List of packages to include in the lambda archive.
        :param file_name: Lambda ZIP archive name.
        :param create_file_if_exists: Create and overwrite the existing output file.
        :param use_docker_non_linux: Use docker on a non-linux environment.
        """
        asset_path = LambdaPackaging(
            include_paths=include,
            work_dir=work_dir,
            out_file=file_name,
            use_docker_non_linux=use_docker_non_linux,
            create_file_if_exists=create_file_if_exists,
        ).package()
        super().__init__(asset_path.as_posix())

    @property
    def is_inline(self) -> bool:
        return False


class LambdaPackaging:
    """
    EXCLUDE_DEPENDENCIES - List of libraries already included in the lambda runtime environment. No need to package these.
    EXCLUDE_FILES - List of files not required and therefore safe to be removed to save space.
    """

    EXCLUDE_DEPENDENCIES = {
        "boto3",
        "botocore",
        "docutils",
        "jmespath",
        "pip",
        "python-dateutil",
        "s3transfer",
        "setuptools",
    }
    EXCLUDE_FILES = {"*.dist-info", "__pycache__", "*.pyc", "*.pyo"}

    def __init__(
        self,
        include_paths: List[str],
        work_dir: Path = Path(__file__).resolve().parent,
        out_file: str = str(uuid.uuid4())[:8],
        create_file_if_exists: bool = True,
        use_docker_non_linux: bool = True,
    ) -> None:
        self._include_paths = include_paths
        self._zip_file = out_file.replace(".zip", "")
        self.work_dir = work_dir
        self.build_dir = self.work_dir / ".build"
        self.requirements_dir = self.build_dir / "requirements"
        self.requirements_txt = self.requirements_dir / "requirements.txt"
        self.use_docker_non_linux = use_docker_non_linux
        self.create_file_if_exists = create_file_if_exists

    @property
    def path(self) -> Path:
        return self.work_dir.joinpath(self._zip_file + ".zip").resolve()

    def package(self) -> Path:
        logging.info(f"Build directory: {self.build_dir}")
        try:
            os.chdir(self.work_dir.as_posix())
            logging.info(f"Working directory: {Path.cwd()}")
            if not self._prepare_build():
                return self.path
            self._build_lambda()
            self._package_lambda()
            return self.path
        except requests.exceptions.ConnectionError:
            raise Exception("Could not connect to Docker daemon.")
        except Exception as ex:
            raise Exception("Error during build.", str(ex))

    def _prepare_build(self) -> bool:
        shutil.rmtree(self.build_dir, ignore_errors=True)
        self.requirements_dir.mkdir(parents=True)
        if self.path.is_file() and self.create_file_if_exists is False:
            logging.info("Hash matches, no need for a new file")
            return False

        logging.info(f"Exporting poetry dependencies: {self.requirements_txt}")
        result = os.system(
            f"poetry export --without-hashes --format requirements.txt --output {self.requirements_txt}"
        )

        if result != 0:
            raise EnvironmentError(
                "Version of your poetry is not compatible - please update to 1.0.0b1 or newer"
            )
        return True

    def _build_lambda(self) -> None:
        if is_linux() or self.use_docker_non_linux is False:
            self._build_natively()
        else:
            self._build_in_docker()
        self._remove_bundled_files()

    def _build_in_docker(self) -> None:
        """
        Build lambda dependencies in a container as-close-as-possible to the actual runtime environment.
        """
        logging.info("Installing dependencies [running in Docker]...")
        client = docker.from_env()
        client.containers.run(
            image=BUILD_IMAGE,
            command="/bin/sh -c 'python3.9 -m pip install --target /var/task/ --requirement /var/task/requirements.txt && "
            "find /var/task -name \\*.so -exec strip \\{{\\}} \\;'",
            remove=True,
            volumes={
                self.requirements_dir.as_posix(): {"bind": "/var/task", "mode": "rw"}
            },
            user=0,
        )

    def _build_natively(self) -> None:
        """
        Build lambda dependencies natively on linux. Should be the same architecture though.
        """
        logging.info("Installing dependencies [running on Linux]...")
        req = self.requirements_dir / "requirements.txt"
        if (
            os.system(
                f"/bin/sh -c 'python3.9 -m pip install -q --target {self.requirements_dir} --requirement {req} && "
                f"find {self.requirements_dir} -name \\*.so -exec strip \\{{\\}} \\;'"
            )
            != 0
        ):
            raise Exception(
                "Error running build in Docker. Make sure Docker daemon is running on your machine."
            )

    def _package_lambda(self) -> None:
        logging.info(
            f"Moving required dependencies to the build directory: {self.build_dir}"
        )
        for req_dir in self.requirements_dir.glob("*"):
            shutil.move(str(req_dir), str(self.build_dir))
        shutil.rmtree(self.requirements_dir, ignore_errors=True)

        logging.info("Copying 'include' resources:")
        for include_path in self._include_paths:
            logging.info(f"    -  {(Path.cwd() / include_path).resolve()}")
            os.system(f"cp -R {include_path} {self.build_dir}")

        zip_file_path = (self.work_dir / self._zip_file).resolve()
        logging.info(f"Packaging application into {zip_file_path}.zip")
        shutil.make_archive(
            str(zip_file_path), "zip", root_dir=str(self.build_dir), verbose=True
        )

    def _remove_bundled_files(self) -> None:
        """
        Remove caches and dependencies already bundled in the lambda runtime environment.
        """
        logging.info("Removing dependencies bundled in lambda runtime and caches:")
        for pattern in self.EXCLUDE_DEPENDENCIES.union(self.EXCLUDE_FILES):
            pattern = str(self.requirements_dir / "**" / pattern)
            logging.info(f"    -  {pattern}")
            files = glob.glob(pattern, recursive=True)
            for file_path in files:
                try:
                    if os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except OSError:
                    logging.error(f"Error while deleting file: {file_path}")
