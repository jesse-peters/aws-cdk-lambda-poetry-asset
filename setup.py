from pathlib import Path
import setuptools
import toml

this_directory = Path(__file__).parent

init_file = {}
exec(
    (this_directory / "aws_cdk_lambda_poetry_asset/__init__.py").read_text(), init_file
)


def _parse_pyproject_toml(pyproject_path):
    pyproject_text = pyproject_path.read_text()
    pyproject_data = toml.loads(pyproject_text)
    poetry_data = pyproject_data["tool"]["poetry"]
    install_requires = []
    for dependency in poetry_data["dependencies"]:
        print(dependency)
        install_requires.append(dependency)
    print(install_requires)
    setup_data = {
        "install_requires": install_requires,
    }
    return setup_data


def _setup():
    pyproject_path = Path("pyproject.toml")
    setup_data = _parse_pyproject_toml(pyproject_path)

    setuptools.setup(
        name="aws_cdk_lambda_poetry_asset",
        version=init_file["__version__"],
        packages=["aws_cdk_lambda_poetry_asset"],
        include_package_data=True,
        license=init_file["__license__"],
        description="Package poetry dependencies for lambda function in AWS CDK. ",
        url="https://github.com/jesse-peters/aws-cdk-lambda-poetry-asset",
        **setup_data,
    )


if __name__ == "__main__":
    _setup()
