.PHONY: test lint type format all

test:	
	pytest --cov=calmoji --cov-report=term-missing

lint:
	ruff check .

type:
	mypy forge

format:
	black .

all: format lint type test
