@echo off
echo Running Mypy...
mypy --ignore-missing-imports earwax tests
echo Running Flake8...
flake8 earwax tests