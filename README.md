# AWS CDK Lambda Asset

## Setup

#### [Install poetry](https://github.com/sdispater/poetry#installation)
```commandline
curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python - -p
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