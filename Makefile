.PHONY: help venv vulnerability-scan lint test

.DEFAULT: help
help:
	@echo "make venv"
	@echo "    activates the virtual environment with pipenv (eg $ pipenv shell)"
	@echo " "
	@echo "make vulnerability-scan"
	@echo "    runs $ pipenv check to look for vulnerabilities in Python packages used"
	@echo " "
	@echo "make lint"
	@echo "    runs mypy"
	@echo " "
	@echo "make test"
	@echo "    runs the tests"
	@echo " "
	@echo "make docs"
	@echo "    builds the html docs which becomes available under docs/_build/html"
	@echo " "
	@echo "make serve-docs"
	@echo "    serves the docs from docs/_build/html by making it available under http://127.0.0.1:8088/_build/html/"

venv:
	pipenv shell

vulnerability-scan:
	pipenv check . --verbose

lint:
	mypy falcon_caching --ignore-missing-imports

test:
	pytest

docs:
	cd docs && \
	make html

serve-docs:
	cd docs && \
	python -m http.server 8088
