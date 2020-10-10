@echo off
rd /s /q build dist earwax.egg-info
python setup.py bdist_wheel
twine upload dist/*
