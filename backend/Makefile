.PHONY: install dev test lint fmt up down migrate revision seed openapi

install:
	pip install -r requirements-dev.txt

up:            ## start backend stack (Postgres + API)
	docker compose up --build

down:
	docker compose down

test:          ## run tests (set TEST_DATABASE_URL for API tests)
	pytest

lint:
	ruff check .

fmt:
	ruff check --fix .

migrate:       ## apply migrations
	alembic upgrade head

revision:      ## autogenerate a migration: make revision m="message"
	alembic revision --autogenerate -m "$(m)"

seed:          ## seed catalog (axes, archetypes, scenarios)
	python -m app.seed

openapi:       ## export the OpenAPI spec to the frontend contract
	python -c "import json,app.main as m; open('../frontend/openapi.json','w').write(json.dumps(m.app.openapi(), ensure_ascii=False, indent=2))"
