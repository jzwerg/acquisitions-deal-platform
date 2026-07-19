# Standard task interface across the portfolio: up / down / demo / test / logs.
.DEFAULT_GOAL := help
.PHONY: help up down logs ps seed embed demo test

help: ## List available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-8s\033[0m %s\n", $$1, $$2}'

up: ## Boot the full stack
	docker compose up --build

down: ## Stop the stack and remove volumes
	docker compose down -v

logs: ## Tail service logs
	docker compose logs -f

ps: ## Show running services
	docker compose ps

seed: ## Load deterministic synthetic mandates + listings (needs the stack up)
	docker compose exec api python -m app.seed

embed: ## Compute + store embeddings for seeded data (mock backend by default)
	docker compose exec api python -m app.embed

demo: ## Headline demo — kill a worker mid-deal (resume) + decline/timeout (archive)
	./scripts/demo.sh

test: ## Run the Python test suite (workflow-replay test + matching eval)
	pytest -q
