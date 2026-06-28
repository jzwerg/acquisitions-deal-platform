# Standard task interface across the portfolio: up / down / demo / test / logs.
.DEFAULT_GOAL := help
.PHONY: help up down logs ps seed demo test

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

demo: ## Headline demo — kill a worker mid-deal, assert the workflow resumes (TODO: wire up — see MILESTONE.md)
	@echo "TODO: start a deal, kill the worker mid-flight, assert exactly-once resume; force a decline/timeout to assert clean archival."

test: ## Run the Python test suite (workflow-replay test + matching eval)
	pytest -q
