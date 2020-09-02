set -ex

echo "Running formatting tests..."

black . --check --line-length 79
flake8
bandit . -r -lll

echo "Running pytests..."
python3 -m pytest -s
