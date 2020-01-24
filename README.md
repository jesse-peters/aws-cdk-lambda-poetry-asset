[![pipeline status](https://gitlab.com/josef.stach/aws-cdk-lambda-asset/badges/master/pipeline.svg)](https://gitlab.com/josef.stach/aws-cdk-lambda-asset/commits/master)
[![coverage report](https://gitlab.com/josef.stach/aws-cdk-lambda-asset/badges/master/coverage.svg)](https://gitlab.com/josef.stach/aws-cdk-lambda-asset/commits/master)

# AWS CDK Lambda Asset

## About

AWS CDK currently supports 3 kinds of "Assets":

* [InlineCode](https://docs.aws.amazon.com/cdk/api/latest/docs/@aws-cdk_aws-lambda.InlineCode.html) - useful for one-line-lambdas
* [AssetCode](https://docs.aws.amazon.com/cdk/api/latest/docs/@aws-cdk_aws-lambda.AssetCode.html) - one-file lambdas without dependencies
* [S3Code](https://docs.aws.amazon.com/cdk/api/latest/docs/@aws-cdk_aws-lambda.S3Code.html) - existing lambda packages already uploaded in an S3 bucket 

There is, however, no support for more complex lambda function which require third party dependencies. 
This repository presents one possible approach to lambda packaging. 

The construct is aware of libraries bundled in the AWS lambda runtime and automatically removes those for you to save space.

It also counts with compiled C dependencies such as NumPy and takes care of library stripping.  

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
from aws_cdk import core, aws_lambda
from aws_cdk_lambda_asset.zip_asset_code import ZipAssetCode

class MyStack(core.Stack):

    def __init__(self, app: core.App, id: str, **kwargs) -> None:
        super().__init__(app, id, **kwargs)
        work_dir = Path(__file__).parents[1]
        aws_lambda.Function(
            scope=self,
            id='MyLambda',
            code=ZipAssetCode(work_dir=work_dir, include=['functions', 'business_logic'], file_name='my-lambda.zip'),
            handler='functions/my_lambda.lambda_handler',
            runtime=aws_lambda.Runtime.PYTHON_3_7
        )
```

## License
This code is released under MIT license. Developed at [Bulletproof AI](https://www.bulletproof.ai).

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
poetry run pytest --cov-report term-missing --cov=aws_cdk_lambda_asset tests
```
