@echo off
rd /s /q build dist
python setup.py bdist_wheel
twine upload dist/*
