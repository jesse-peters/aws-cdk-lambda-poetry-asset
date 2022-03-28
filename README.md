# AWS CDK Lambda Poetry Asset

## About
This is the cdk v2 version of the original asset, which is available at [gitlab](https://gitlab.com/josef.stach/aws-cdk-lambda-asset).


AWS CDK currently supports 3 kinds of "Assets":

* [InlineCode](https://docs.aws.amazon.com/cdk/api/latest/docs/@aws-cdk_aws-lambda.InlineCode.html) - useful for one-line-lambdas
* [AssetCode](https://docs.aws.amazon.com/cdk/api/latest/docs/@aws-cdk_aws-lambda.AssetCode.html) - one-file lambdas without dependencies
* [S3Code](https://docs.aws.amazon.com/cdk/api/latest/docs/@aws-cdk_aws-lambda.S3Code.html) - existing lambda packages already uploaded in an S3 bucket

There is, however, no support for more complex lambda function which require third party dependencies.
This repository presents one possible approach to lambda packaging.

The construct is aware of libraries bundled in the AWS lambda runtime and automatically removes those for you to save space.

It also counts with compiled C dependencies such as NumPy and takes care of library stripping.

By setting the `create_file_if_exists` to `False` you can use it with a caching system, like Github Actions `actions/cache@v3`. It will only run the build if the file doesnt exist at the output path already.

## Usage
Suppose your project's directory structure looks like this:
```
my-project
├── business_logic
│   └── backend.py
└── functions
    └── my_lambda.py
```

Then your stack would be:

```python
from pathlib import Path
from aws_cdk import aws_lambda
from aws_cdk_lambda_poetry_asset.zip_asset_code import ZipAssetCode

class MyStack(core.Stack):

    def __init__(self, app: core.App, id: str, **kwargs) -> None:
        super().__init__(app, id, **kwargs)
        work_dir = Path(__file__).parents[1]
        aws_lambda.Function(
            scope=self,
            id='MyLambda',
            code=ZipAssetCode(
                work_dir=work_dir,
                include=['functions', 'business_logic'],
                file_name='my-lambda.zip',
                create_file_if_exists=False
            )
            handler='functions/my_lambda.lambda_handler',
            runtime=aws_lambda.Runtime.PYTHON_3_9
        )
```
## Setup

#### [Install poetry](https://github.com/sdispater/poetry#installation)
```commandline
pip install poetry
```

#### Install dependencies
```commandline
poetry update
```

#### Run tests
Start docker first.
```commandline
poetry run pytest --cov-report term-missing --cov=aws_cdk_lambda_poetry_asset tests
```


## Create a release

This project will automatically create a github release when a PR is merged into the `main` branch. The title of the PR must adhere to [angular commit message format](https://github.com/angular/angular/blob/master/CONTRIBUTING.md#-commit-message-format) in order for it to calculate a new version number.

### Example PR titles:

`feat: mindblowing feature`

`fix: bug thats been around for ever`

### Types
From angular documentation

Must be one of the following:

* **build**: Changes that affect the build system or external dependencies (example scopes: gulp, broccoli, npm)
* **ci**: Changes to our CI configuration files and scripts (example scopes: Circle, BrowserStack, SauceLabs)
* **docs**: Documentation only changes
* **feat**: A new feature
* **fix**: A bug fix
* **perf**: A code change that improves performance
* **refactor**: A code change that neither fixes a bug nor adds a feature
* **test**: Adding missing tests or correcting existing tests
## License
This code is released under MIT license.
