.DEFAULT_GOAL := help

.PHONY: help install test stubs docs docs-deploy clean publish

help: ## Show available targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  %-12s %s\n", $$1, $$2}'

install: ## Create/sync the environment (incl. dev deps)
	uv sync

test: ## Run the test suite
	uv run pytest tests/ -q

stubs: ## Regenerate .pyi stubs for the dynamic feat wrappers
	uv run python tools/gen_feat_stubs.py

docs: ## Serve the docs locally with live reload
	uv run --group docs mkdocs serve

docs-deploy: ## Build and deploy the docs to GitHub Pages
	uv run --group docs mkdocs gh-deploy --strict
	rm -rf site

publish: test ## Runs test first. Then bump patch version, build and publish to PyPI
	uv version --bump patch
	rm -rf dist
	uv build
	uv publish

clean: ## Remove caches and build artifacts
	rm -rf .pytest_cache dist build site
	find . -type d -name __pycache__ -not -path './.venv/*' -exec rm -rf {} +
