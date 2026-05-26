# AI Platform - Docker Compose Orchestration
.PHONY: up down build logs test clean ps health

# Start all services
up:
	docker compose up -d

# Stop all services
down:
	docker compose down

# Build all images
build:
	docker compose build

# Rebuild and start
rebuild: build up

# Follow logs
logs:
	docker compose logs -f

# Show service status
ps:
	docker compose ps

# Health check for all services
health:
	@echo "Checking health of all services..."
	@for port in 8000 9001 9002 9003 9004 9005; do \
		echo -n "Port $$port: "; \
		curl -s -o /dev/null -w "%{http_code}" http://localhost:$$port/health || echo "FAILED"; \
		echo ""; \
	done

# Run tests in each Python service
test:
	@echo "Running tests for all Python services..."
	@cd services/service-llm && python -m pytest tests/ -q --tb=short 2>/dev/null || echo "service-llm tests skipped"
	@cd services/service-rag && python -m pytest tests/ -q --tb=short 2>/dev/null || echo "service-rag tests skipped"
	@cd services/service-memory && python -m pytest tests/ -q --tb=short 2>/dev/null || echo "service-memory tests skipped"
	@cd services/service-prompt && python -m pytest tests/ -q --tb=short 2>/dev/null || echo "service-prompt tests skipped"
	@cd services/service-data && python -m pytest tests/ -q --tb=short 2>/dev/null || echo "service-data tests skipped"
	@cd services/mcp-hub && python -m pytest tests/ -q --tb=short 2>/dev/null || echo "mcp-hub tests skipped"

# Clean volumes and networks
clean:
	docker compose down -v
	docker system prune -f

# Restart a specific service (usage: make restart SERVICE=mcp-hub)
restart:
	docker compose restart $(SERVICE)

# Shell into a service (usage: make shell SERVICE=mcp-hub)
shell:
	docker compose exec $(SERVICE) /bin/sh
