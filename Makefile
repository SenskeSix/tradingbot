.PHONY: fmt lint test up

fmt:
	python -m black app tests

lint:
	python -m ruff check app tests

test:
	pytest

up:
	docker-compose up --build
