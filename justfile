pytest-args := '-vv'
poetry_cmd := 'poetry run'

# Lists what recipes are available
default:
  @just --list


###############################################################################
################################# Project Dependencies ########################
###############################################################################

# Updates current venv to match lockfile
devenv:
    poetry install

# Doesnt work inside this command yet
# Experimental: https://github.com/python-poetry/poetry/issues/2684#issuecomment-1076560832
_deps-outdated:
    poetry show --outdated | grep --file=<(poetry show --tree | grep '^\w' | cut -d' ' -f1 | sed 's/.*/^&\\s/')

# Updates lockfile and local venv to latest valid versions
deps-update:
    poetry update

###############################################################################
################################# Local Testing ###############################
###############################################################################

# Run python tests
test args=pytest-args:
    {{poetry_cmd}} coverage run -m pytest -m "not integration_app and not cdk and not snapshot" {{args}}

# Lint Python code
lint:
    {{poetry_cmd}} flake8 .

# Format Python code
format:
    {{poetry_cmd}} black .

# Sort imports
sort-imports:
    {{poetry_cmd}} isort .


###############################################################################
################################# CI Testing ##################################
###############################################################################
# CI: Run tests (unit)
ci-test-unit:
    @{{poetry_cmd}} coverage run -m pytest -vv -m "not integration_app and not cdk and not snapshot" -p no:sugar --junitxml=results.xml

# CI: Generate test coverage artifacts
ci-test-report:
    {{poetry_cmd}} coverage report | tee pytest-coverage.txt
    {{poetry_cmd}} coverage html -d output/coverage

# CI: Sort imports
ci-sort-imports:
    {{poetry_cmd}} isort --check --diff .

# CI: Run code format check
ci-format:
    {{poetry_cmd}} black . --check
