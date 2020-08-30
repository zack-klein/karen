set -ex

flake8
black . --check --line-length 79
bandit . -r -lll
