.PHONY: update docs quality Quality tests clean

update:
	pip install -r requirements-dev.txt
	pip install -e .

docs:
	sphinx-build -W -n -b html docs ./build/sphinx/html

quality:
	python setup.py check --strict --metadata
	python setup.py --quiet sdist && twine check dist/*
	check-manifest
	flake8 src tests

Quality:  # not used in tests
	vulture --exclude=build/ src tests setup.py

tests:
	py.test tests

clean:
	-find src "(" -name '*.so' -or -name '*.egg' -or -name '*.pyc' -or -name '*.pyo' ")" -delete
	-find src -type d -name __pycache__ -exec rm -r {} \;
	-rm -rf .tox .cache build dist
