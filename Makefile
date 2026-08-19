.PHONY: help install install-dev test test-cov lint fmt up up-shim down logs demo smoke seed clean

PY?=python
COMPOSE?=docker compose

help:
	@echo "make install       install runtime deps"
	@echo "make install-dev   install runtime + dev deps (ruff, pytest-cov)"
	@echo "make up            bring up the platform"
	@echo "make up-shim       bring up the platform + the kserve shim"
	@echo "make down          stop everything"
	@echo "make logs          tail logs"
	@echo "make seed          create minio buckets"
	@echo "make demo          run the end-to-end demo (bootstrap + train + deploy + drift)"
	@echo "make smoke         run the offline core-lifecycle smoke (no docker/cloud)"
	@echo "make test          run unit tests"
	@echo "make test-cov      run unit tests with coverage"
	@echo "make lint          ruff check"
	@echo "make fmt           ruff format"
	@echo "make clean         drop caches"

install:
	$(PY) -m pip install -r requirements.txt
	$(PY) -m pip install -e .

install-dev: install
	$(PY) -m pip install pytest-cov ruff

test:
	pytest

test-cov:
	pytest --cov=src --cov-report=term-missing --cov-report=xml

lint:
	ruff check src tests

fmt:
	ruff format src tests

up:
	$(COMPOSE) up -d

up-shim:
	$(COMPOSE) --profile shim up -d

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=200

seed:
	bash scripts/seed_minio.sh

demo:
	bash scripts/demo.sh

smoke:
	$(PY) scripts/smoke.py

clean:
	rm -rf .pytest_cache .ruff_cache __pycache__ build dist *.egg-info coverage.xml .coverage
