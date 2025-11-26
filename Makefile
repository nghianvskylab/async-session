lint:
	@echo "Running lint"
	@poetry run pysen run lint

format:
	@echo "Running format"
	@poetry run pysen run format

migrate:
	@echo "Running migrate"
	@poetry run alembic upgrade head

migrate-down:
	@echo "Running migrate down"
	@poetry run alembic downgrade -1

migrate-status:
	@echo "Checking migration status"
	@poetry run alembic current
	@echo "\nMigration history:"
	@poetry run alembic history

migrate-create:
	@echo "Creating new migration (usage: make migrate-create NAME=migration_name)"
	@poetry run alembic revision --autogenerate -m "$(NAME)"

start:
	@echo "Running start"
	@poetry run uvicorn api.main:app --reload

test:
	@echo "Running test"
	@poetry run pytest

test-coverage:
	@echo "Running test coverage"
	@poetry run pytest --cov=api

build-docker:
	@echo "Building Docker images"
	@docker compose -f .infrastructure/docker-compose.yml build

stop:
	@echo "Stopping Docker containers"
	@docker compose -f .infrastructure/docker-compose.yml down

logs:
	@echo "Showing Docker logs"
	@docker compose -f .infrastructure/docker-compose.yml logs -f

migrate-docker:
	@echo "Running migrations in Docker container"
	@docker compose -f .infrastructure/docker-compose.yml exec -T fastapi alembic upgrade head

start-docker:
	@echo "Starting stack via Docker Compose"
	@docker compose -f .infrastructure/docker-compose.yml up --build