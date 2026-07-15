.DEFAULT_GOAL := help

.PHONY: help install export test stubs prepare check docs-main docs-api docs preview api-preview serve-docs docs-deploy clean publish

DOCS_DIR := _docs
PDOC_PORT := 8081
DOCS_PORT := 8000

help: ## Show available targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  %-12s %s\n", $$1, $$2}'

install: ## Create/sync the environment, including docs deps (nbdev, pdoc)
	uv sync --group docs

export: ## Export nbs/ notebooks -> the qrt/ package. qrt/**/*.py is generated, not committed
	uv run --group docs nbdev-export

test: export ## Export, then run notebook tests (nbdev) and the pytest suite
	uv run --group docs nbdev-test
	uv run pytest tests/ -q

stubs: ## Regenerate .pyi stubs for the dynamic feat wrappers
	uv run python tools/gen_feat_stubs.py

prepare: ## Export, test, clean notebook metadata, and refresh README.md from nbs/index.ipynb
	uv run --group docs nbdev-prepare

check: prepare ## Run prepare and fail if it produced uncommitted generated changes (nbs/README drift)
	git diff --exit-code

docs-main: export ## Build the nbdev/Quarto narrative site (must run in active venv)
	uv run --group docs nbdev-docs

docs-api: export ## Build the pdoc API reference into _docs/api (must run after docs-main)
	rm -rf "$(DOCS_DIR)/api"
	uv run --group docs python -m pdoc qrt --output-directory "$(DOCS_DIR)/api" --docformat google

docs: clean ## Clean, then build the complete site: narrative (nbdev) + API reference (pdoc)
	$(MAKE) docs-main
	$(MAKE) docs-api

preview: export ## Live-reloading preview of the narrative docs
	uv run --group docs nbdev-preview

api-preview: export ## Live-reloading preview of the pdoc API reference
	uv run --group docs python -m pdoc qrt --docformat google --host localhost --port $(PDOC_PORT)

serve-docs: ## Serve the already-built combined site (run `make docs` first)
	uv run python -m http.server $(DOCS_PORT) --directory "$(DOCS_DIR)"

docs-deploy: docs ## Build the complete site and publish it to GitHub Pages
	uv run --group docs quarto publish gh-pages nbs --no-render --no-prompt

publish: test ## Runs test first. Then bump patch version, build and publish to PyPI
	uv version --bump patch
	rm -rf dist
	uv build
	uv publish

clean: ## Remove docs/build artifacts (does not touch nbs/ or the generated qrt/ package)
	rm -rf "$(DOCS_DIR)" _proc .quarto nbs/.quarto
	find . -type d -name __pycache__ -not -path './.venv/*' -exec rm -rf {} +

