.PHONY: help up down restart logs ps neo4j build clean

help:
	@echo "NetContext Orchestration Commands:"
	@echo "  make up       - Build and start all microservices (Neo4j, Ingestion, RAG, UI)"
	@echo "  make neo4j    - Start only the Neo4j database service"
	@echo "  make down     - Stop all running containers"
	@echo "  make logs     - Follow logs across all microservices"
	@echo "  make build    - Rebuild Docker images without cache"
	@echo "  make clean    - Stop containers and remove persistent volumes"

up:
	docker compose up --build -d

neo4j:
	docker compose up -d neo4j

down:
	docker compose down

restart:
	docker compose down && docker compose up -d

logs:
	docker compose logs -f

ps:
	docker compose ps

build:
	docker compose build --no-cache

clean:
	docker compose down -v
