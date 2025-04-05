## Project specific comments
.PHONY: start
start:
	@./scripts/launch.sh

####----Basic configurations----####
.PHONY: pre-commit
install_pre_commit: ## configure and install pre commit tool
	@uv run pre-commit install

uninstall_pre_commit: ## configure and install pre commit tool
	@uv run pre-commit uninstall

.PHONY: install
install: ## Install the uv and python environment
	@echo "🚀 Creating virtual environment using pyenv and uv"
	@uv sync

.PHONY: check_project
check_project: ## Run code quality tools.
	@echo "🚀 Checking Uv lock file consistency with 'pyproject.toml': Running uv lock --locked"
	@uv lock --locked
	@echo "🚀 Linting code: Running pre-commit"
	@uv run pre-commit run -a

	# This is different from the gitleaks pre-commit since it checks also unstaged files
	@gitleaks protect --no-banner --verbose

.PHONY: test
test: ## Test the code with pytest.
	@echo "🚀 Testing code: Running pytest"
	@uv run pytest --cov --cov-config=pyproject.toml --cov-report=xml tests

####----Documentation----####
.PHONY: docs
docs: ## Launch mkdocs documentation locally
	uv run mkdocs serve

docs_build: ## Build mkdocs for local test
	uv run mkdocs build

docs_launch_local: ## Launch mkdocs documentation locally with the local building artefacts
	uv run mkdocs build
	uv run mkdocs serve -v --dev-addr=0.0.0.0:8000

docs_deploy: ## Deploy mkdocs documentation to github pages
	uv run mkdocs build -c -v --site-dir public
	uv run mkdocs gh-deploy --force

docs_public: ## Build mkdocs for official online release
	uv run mkdocs build -c -v --site-dir public

### Project specific tasks
.PHONY: project
launch_py3: # Launch the main file with python 3
	@export PYTHONPATH=$(pwd) && python3 app/main.py
launch_py: # Launch the main file with python
	@export PYTHONPATH=$(pwd) && python app/main.py

### Git related tasks
.PHONY: git
commit: # Commit changes with commitizen
	@uv run cz commit

####----Docker----####
.PHONY: docker

# configure the aws cli with the credentials: aws configure
login:
	aws ecr get-login-password | docker login --username AWS --password-stdin 381962741642.dkr.ecr.eu-central-1.amazonaws.com

create_network: ## create the docker network for the project
	docker network create bakky

launch: ## launch the python application containers
	@echo "🚀 Launching bakky"
	chmod 775 ./scripts/launch_docker.sh
	./scripts/launch_docker.sh

launch_clean: ## launch the python application containers cleaning old data
	@echo "🚀 Launching bakky in clean environment (Prefect, Redis)"
	sudo rm -rf ~/.prefect/* && sudo rm -rf /data/project/bakky && sudo rm -rf /data/project/bakky/redis_data
	chmod 775 ./scripts/launch_docker.sh
	./scripts/launch_docker.sh

launch_dev: ## launch the python application containers
	@echo "🚀 Launching bakky with mounts in current folder"
	sudo rm -rf ~/.prefect/* && sudo rm -rf /tmp/volumes/bakky/* && sudo rm -rf /tmp/volumes/redis_data/*
	chmod 775 ./scripts/launch_dev.sh
	./scripts/launch_dev.sh

launch_redis: ## launch redis and redis insight
	docker-compose -p bakky up --build -d bakky_redis_insight

launch_prefect: ## launch the bakky project containers only
	docker-compose -p bakky up --build -d bakky_worker

launch_db: ## launch the database container only
	docker-compose -p bakky up --build -d bakky_database

check: ## check the status of the docker containers
	docker ps -a | grep "bakky"

check_logs: ## check the logs of the application container
	docker logs -t app

check_exec: ## exec bash in the python app container
	docker exec -it app /bin/bash

check_redis:
	docker logs -t bakky_redis

check_db:
	docker logs -t bakky_database

check_server:
	docker logs -t bakky_server

check_worker:
	docker logs -t bakky_worker

stop: ## stop all containers
	docker-compose -p bakky down
	# docker-compose down -v

stop_clear: ## stop containers and clean the volumes
	docker-compose -p bakky down -v

clean_volumes: ## clean the docker volumes
	docker volume prune

####----Project----####
.PHONY: help
help: ## Ask for help in the Makefile
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: project_clean
clean: ## Clean the projects of unwanted cached folders
	rm -rf **/.ipynb_checkpoints **/.pytest_cache **/__pycache__ **/**/__pycache__ ./notebooks/ipynb_checkpoints .pytest_cache ./dist ./volumes

.PHONY: project_restore
restore: ## Restore the projects to the start (hard clean)
	rm -rf **/.ipynb_checkpoints **/.pytest_cache **/__pycache__ **/**/__pycache__ ./notabooks/ipynb_checkpoints .pytest_cache ./dist .venv pdm.lock

.DEFAULT_GOAL := help
