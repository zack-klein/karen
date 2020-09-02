set -ex

echo "Running formatting tests..."

# python3 -m black . --check --line-length 79
python3 -m flake8
python3 -m bandit . -r -lll

echo "Running pytests..."
python3 -m pytest -s
