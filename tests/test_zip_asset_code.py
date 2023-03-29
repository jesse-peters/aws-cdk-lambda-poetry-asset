import os
import platform
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from typing import List
from unittest.mock import patch

import pytest
import requests

from aws_cdk_lambda_poetry_asset import zip_asset_code
from aws_cdk_lambda_poetry_asset.zip_asset_code import LambdaPackaging, ZipAssetCode


def not_linux() -> bool:
    return False


class TestRemoveBundledFiles(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.packaging_class = LambdaPackaging(
            include_paths=[],
            work_dir=self.temp_dir,
            use_docker=False,
            out_file="asset.zip",
            dependencies_to_exclude=["urllib3"],
            include_so_files=False,
        )
        self.packaging_class.build_dir = self.temp_dir
        self.packaging_class.dependencies_to_exclude = {"exclude_*.txt"}
        self.packaging_class.EXCLUDE_FILES = {"exclude_*.json"}

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    @patch("logging.info")
    def test_remove_bundled_files(self, mock_logging_info):
        # Create files and directories to test
        files_to_exclude = [
            os.path.join(self.temp_dir, "exclude_1.txt"),
            os.path.join(self.temp_dir, "exclude_2.txt"),
            os.path.join(self.temp_dir, "exclude_3.json"),
        ]

        files_to_keep = [
            os.path.join(self.temp_dir, "keep_1.txt"),
            os.path.join(self.temp_dir, "keep_2.json"),
        ]

        for file in files_to_exclude + files_to_keep:
            with open(file, "w") as f:
                f.write("dummy content")

        self.packaging_class._remove_bundled_files()

        for file in files_to_exclude:
            self.assertFalse(os.path.exists(file))

        for file in files_to_keep:
            self.assertTrue(os.path.exists(file))


def prepare_workspace(path: Path) -> List[str]:
    # Prepare a sample requirements.txt
    (path / "pyproject.toml").write_text(
        """[tool.poetry]
         name = "my_product"
         version = "0.1"
         description = ""
         authors = ["Stuff <fake@example.fake>"]

         [tool.poetry.dependencies]
         python = "^3.9"
         boto3 = "^1.9"
         requests = "^2.20"
         """
    )

    (path / "setup.cfg").write_text(
        """[install]
        prefix=
        """
    )

    # Create module dirs
    module_dirs = ["product_1", "product_2"]
    for m in module_dirs:
        (path / m).mkdir()

    return module_dirs


def test_packaging_linux(tmp_path, monkeypatch):
    def linux() -> bool:
        return True

    monkeypatch.setattr(zip_asset_code, "is_linux", linux)
    include_paths = prepare_workspace(tmp_path)

    asset = LambdaPackaging(
        include_paths=include_paths,
        work_dir=tmp_path,
        use_docker=False,
        out_file="asset.zip",
        dependencies_to_exclude=["urllib3"],
        python_dependencies_to_exclude=["requests"],
        include_so_files=False,
    ).package()
    assert sorted(next(os.walk(str(tmp_path / ".build")))[1]) == [
        "product_1",
        "product_2",
        "python",
    ]
    assert sorted(
        next(os.walk(str(tmp_path / ".build/python/lib/python3.9/site-packages")))[1]
    ) == ["bin", "dateutil"]
    assert asset.exists()
    assert asset.is_file()
    zipfile.ZipFile(asset)


@pytest.mark.skipif(
    platform.system().lower() == "linux",
    reason="Requires Docker daemon running (or docker-in-docker)",
)
def test_packaging_not_linux(tmp_path, monkeypatch):
    def not_linux() -> bool:
        return False

    monkeypatch.setattr(zip_asset_code, "is_linux", not_linux)
    include_paths = prepare_workspace(tmp_path)

    asset = LambdaPackaging(
        include_paths=include_paths,
        work_dir=tmp_path,
        out_file="asset.zip",
        docker_arguments={"platforms": ["linux/amd64"]},
        include_so_files=False,
    ).package()

    assert sorted(next(os.walk(str(tmp_path / ".build")))[1]) == [
        "product_1",
        "product_2",
        "python",
    ]
    assert asset.exists()
    assert asset.is_file()


def test_build_error(tmp_path, monkeypatch):
    def prepare_build():
        raise requests.exceptions.ConnectionError("Can not connect to Docker")

    monkeypatch.setattr(LambdaPackaging, "_prepare_build", prepare_build)

    with pytest.raises(Exception) as ex:
        LambdaPackaging(
            include_paths=(prepare_workspace(tmp_path)),
            work_dir=tmp_path,
            out_file="asset.zip",
        ).package()
    assert "Error during build." in str(ex.value)


def test_linux_detection(monkeypatch):
    def linux() -> str:
        return "Linux"

    def mac() -> str:
        return "Mac"

    monkeypatch.setattr(platform, "system", linux)
    assert zip_asset_code.is_linux()

    monkeypatch.setattr(platform, "system", mac)
    assert not zip_asset_code.is_linux()


def test_zip_asset_code(tmp_path, monkeypatch):
    def linux() -> bool:
        return True

    monkeypatch.setattr(zip_asset_code, "is_linux", linux)
    asset_code = ZipAssetCode(
        work_dir=tmp_path, include=(prepare_workspace(tmp_path)), file_name="asset.zip"
    )

    assert not asset_code.is_inline
    assert asset_code.path.endswith("/asset.zip")


class TestDeleteFileOrDirectory(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = tempfile.mkstemp(dir=self.temp_dir)[1]
        self.packaging_class = LambdaPackaging(
            include_paths=[],
            work_dir=self.temp_dir,
            use_docker=False,
            out_file="asset.zip",
            dependencies_to_exclude=["urllib3"],
            include_so_files=False,
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_delete_directory(self):
        dir_to_delete = os.path.join(self.temp_dir, "dir_to_delete")
        os.mkdir(dir_to_delete)

        self.packaging_class._delete_file_or_directory(dir_to_delete)
        self.assertFalse(os.path.exists(dir_to_delete))

    def test_delete_file(self):
        self.packaging_class._delete_file_or_directory(self.temp_file)
        self.assertFalse(os.path.exists(self.temp_file))


class TestCreateZipArchive(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.packaging_class = LambdaPackaging(
            include_paths=[],
            work_dir=self.temp_dir,
            use_docker=False,
            out_file="asset.zip",
            dependencies_to_exclude=["urllib3"],
            include_so_files=False,
        )

        self.packaging_class.build_dir = self.temp_dir
        self.packaging_class.work_dir = tempfile.mkdtemp()
        self.packaging_class._zip_file = "my_zip_file"

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        shutil.rmtree(self.packaging_class.work_dir)

    @patch("logging.info")
    def test_create_zip_archive(self, mock_logging_info):
        # Create a dummy file in the build directory
        dummy_file_path = os.path.join(self.temp_dir, "dummy_file.txt")
        with open(dummy_file_path, "w") as f:
            f.write("dummy content")

        self.packaging_class._create_zip_archive()

        zip_file_path = os.path.join(
            self.packaging_class.work_dir, self.packaging_class._zip_file + ".zip"
        )
        self.assertTrue(os.path.exists(zip_file_path))

        # Check if the ZIP archive contains the expected content
        with zipfile.ZipFile(zip_file_path, "r") as zip_file:
            zip_file_content = zip_file.namelist()

        self.assertEqual(len(zip_file_content), 1)
        self.assertEqual(zip_file_content[0], "dummy_file.txt")
