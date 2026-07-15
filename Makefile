.DEFAULT_GOAL := help

.PHONY: help install test stubs nb-execute docs docs-deploy clean publish

help: ## Show available targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  %-12s %s\n", $$1, $$2}'

install: ## Create/sync the environment (incl. dev deps)
	uv sync

test: ## Run the test suite
	uv run pytest tests/ -q

stubs: ## Regenerate .pyi stubs for the dynamic feat wrappers
	uv run python tools/gen_feat_stubs.py

nb-execute: ## Re-run docs/*.ipynb in place so they carry saved cell outputs (for local editor preview)
	uv run --group docs jupyter nbconvert --to notebook --execute --inplace docs/demo.ipynb

docs: ## Build the API reference and serve the docs locally with live reload. Must run in active venv!
	uv run --group docs quartodoc build --config docs/_quarto.yml
	quarto preview docs

docs-deploy: ## Build the API reference and publish the docs to GitHub Pages. Must run in active venv!
	uv run --group docs quartodoc build --config docs/_quarto.yml
	quarto publish gh-pages docs --no-prompt

publish: test ## Runs test first. Then bump patch version, build and publish to PyPI
	uv version --bump patch
	rm -rf dist
	uv build
	uv publish

clean: ## Remove caches and build artifacts
	rm -rf .pytest_cache dist build docs/_site docs/.quarto docs/reference
	find . -type d -name __pycache__ -not -path './.venv/*' -exec rm -rf {} +
