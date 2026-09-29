.PHONY: help setup install env db migrate run dev test

PYTHON := python3
VENV := venv
BIN := $(VENV)/bin
PIP_INDEX := https://pypi.org/simple

DB_IMAGE := ci-interview-postgres
DB_CONTAINER := ci-interview-postgres
DB_USER := db_user
DB_NAME := db_name
DB_PORT := 5432

.DEFAULT_GOAL := help

help:
	@echo "Targets:"
	@echo "  make setup    create venv, install deps, .env, database, and migrations"
	@echo "  make run      start the API at http://127.0.0.1:8000/docs"
	@echo "  make dev      setup, then run"
	@echo "  make install  create the virtualenv and install requirements"
	@echo "  make env      copy .env.example to .env when .env is missing"
	@echo "  make db       build the Dockerfile image and start PostgreSQL"
	@echo "  make migrate  apply Alembic migrations"
	@echo "  make test     run pytest"

install:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip --index-url $(PIP_INDEX)
	$(BIN)/pip install -r requirements.txt --index-url $(PIP_INDEX)

env:
	@test -f .env || cp .env.example .env

db:
	@if ! docker start $(DB_CONTAINER) >/dev/null 2>&1; then \
		docker build -t $(DB_IMAGE) . && \
		docker run -d --name $(DB_CONTAINER) -p $(DB_PORT):5432 $(DB_IMAGE); \
	fi
	@for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do \
		docker exec $(DB_CONTAINER) pg_isready -U $(DB_USER) -d $(DB_NAME) >/dev/null 2>&1 && exit 0; \
		sleep 1; \
	done; \
	echo "Postgres did not become ready"; exit 1

migrate: env
	$(BIN)/alembic upgrade head

run:
	$(BIN)/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

setup: install env db migrate

dev: setup run

test:
	$(BIN)/pytest
