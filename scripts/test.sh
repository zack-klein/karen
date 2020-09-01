set -ex

echo "Running formatting tests..."

flake8
black . --check --line-length 79
bandit . -r -lll

echo "Running pytests..."
pytest
