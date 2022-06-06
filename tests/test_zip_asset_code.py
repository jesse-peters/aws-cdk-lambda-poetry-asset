import os
import platform
import zipfile
from pathlib import Path
from typing import List

import pytest
import requests

from aws_cdk_lambda_poetry_asset import zip_asset_code
from aws_cdk_lambda_poetry_asset.zip_asset_code import LambdaPackaging, ZipAssetCode


def prepare_workspace(path: Path) -> List[str]:
    # Prepare a sample requirements.txt
    (path / "pyproject.toml").write_text(
        """[tool.poetry]
         name = "my_product"
         version = "0.1"
         description = ""
         authors = ["DevOps <devops@bulletproof.ai>"]

         [tool.poetry.dependencies]
         python = "^3.9"
         boto3 = "^1.9"
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
    ).package()
    assert sorted(next(os.walk(str(tmp_path / ".build")))[1]) == [
        "product_1",
        "product_2",
        "python",
    ]
    assert sorted(
        next(os.walk(str(tmp_path / ".build/python/lib/python3.9/site-packages")))[1]
    ) == ["bin", "dateutil", "urllib3"]
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
        docker_platforms=["linux/amd64"],
        dependencies_to_exclude=["urllib3"],
    ).package()

    assert sorted(next(os.walk(str(tmp_path / ".build")))[1]) == [
        "bin",
        "dateutil",
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
