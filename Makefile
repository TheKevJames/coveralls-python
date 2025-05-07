help:
	@echo  "Development makefile"
	@echo
	@echo  "Usage: make <target>"
	@echo  "Targets:"
	@echo  "    up      Updates dev/test dependencies"
	@echo  "    deps    Ensure dev/test dependencies are installed"
	@echo  "    check   Checks that build is sane"
	@echo  "    test    Runs all tests"
	@echo  "    style   Auto-formats the code"
	@echo  "    lint    Auto-formats the code and check type hints"

up:
	poetry run poetry update --verbose

deps:
	poetry install --all-extras --verbose

_style:
	$(MAKE) _check
style: deps _style

_check:
	pre-commit run --all-files
check: deps _check

_lint:
	$(MAKE) _check
lint: deps _lint

_test:
	poetry run pytest
test: deps _test

_build:
	poetry build --clean
build: deps _build

ci: check _build _test
