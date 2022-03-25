from pathlib import Path
import setuptools

this_directory = Path(__file__).parent

init_file = {}
exec(
    (this_directory / "aws_cdk_lambda_poetry_asset/__init__.py").read_text(), init_file
)
install_requires = ["aws-cdk-lib >= 2.0.0", "docker >= 5.0.0"]

setuptools.setup(
    name="aws_cdk_lambda_poetry_asset",
    version=init_file["__version__"],
    packages=["aws_cdk_lambda_poetry_asset"],
    include_package_data=True,
    license=init_file["__license__"],
    description="Package poetry dependencies for lambda function in AWS CDK. ",
    url="https://github.com/jesse-peters/aws-cdk-lambda-poetry-asset",
    install_requires=install_requires,
)
