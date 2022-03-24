from pathlib import Path

from setuptools import setup

this_directory = Path(__file__).parent

long_description = ""
# get the version

init_file = {}
exec(
    (this_directory / "aws_cdk_lambda_poetry_asset/__init__.py").read_text(), init_file
)


setup(
    name="aws_cdk_lambda_poetry_asset",
    version=init_file["__version__"],
    packages=["aws_cdk_lambda_poetry_asset"],
    include_package_data=True,
    license=init_file["__license__"],
    long_description=long_description,
)
