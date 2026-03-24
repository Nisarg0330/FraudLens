.PHONY: dev stop build test lint clean logs

# Start infrastructure (Postgres + Redis + Adminer)
dev:
	docker compose up -d

# Stop all services
stop:
	docker compose down

# Run backend locally
run-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

# Run all tests
test:
	cd backend && pytest tests/ -v

# Lint all code
lint:
	cd backend && ruff check .

# View logs
logs:
	docker compose logs -f

# Reset database (destroys all data)
reset-db:
	docker compose down -v
	docker compose up -d

# Run database migrations
migrate:
	cd backend && alembic upgrade head

# Create a new migration
migration:
	cd backend && alembic revision --autogenerate -m "$(msg)"

# Clean up Docker resources
clean:
	docker compose down -v --rmi local
	docker system prune -f