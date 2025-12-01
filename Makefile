.PHONY: install test lint fmt up down demo clean

PY?=python

install:
	$(PY) -m pip install -r requirements.txt
	$(PY) -m pip install -e .

test:
	pytest

lint:
	ruff check src tests

fmt:
	ruff format src tests

up:
	docker compose up -d

down:
	docker compose down

demo:
	bash scripts/demo.sh

clean:
	rm -rf .pytest_cache __pycache__ build dist *.egg-info
