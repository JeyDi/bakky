# Bakky

Plug and play generalize backend system for small and quick projects following best practice standard.

There are a lot of templates, but everytime they are fit to my behaviours.

In this repository I'll put all my expertise and what I have developed over the years in order to use it for personal documentation and as a getting started repository.

Everything open source and should run on-premise without any external service with docker-compose.

I'll try to keep this project maintained and updated meanwhile I'll continue working and learning new things, if you find something strange, you want to discuss and argue about certain topics or propose new things or changes: please open an issue (and try to propose always a solution).

If you find this work useful don't remember to cite me and this repository, if you want you can also contact me for sponsorship or collaboration.

## Requirements

- Python 3.12
- Python uv: for package management
- Docker: for containerization

## Features

I'm trying to be much more modular as possible.

- Python 3.12 with uv, ruff, pydantic and pydantic-settings
- Usage of Hexagonal design system
- Python FastAPI Backend with best practices
- Authentication layer
- Docker and Docker-compose
- Parquet and Delta integration with Polars and Duckdb
- MongoDB usage
- ORM mode with SQLAlchemy with Postgres
- Manage table using yaml definition
- Generalize OTEL log system with logfire on-premise
- Cache system with Redis
- Queue system with RabbitMQ
- Granian or Uvicorn support
- Documentation with MKDocs
- Github and Gitlab CI/CD templates
- Vector database
- CLI interface using typer
- MKDocs documentation about this project
- Tests with pytest and mockups

### Extra

- Admin pannel and auth management
- Envoy proxy
- Certbot
- [Conventional commit](https://www.conventionalcommits.org/en/v1.0.0/)
- Pre-commit

## How to use it

1. Clone the repository
2. Create a new `.env` based on `.env.example`:

   ```bash
   cp .env.example .env
   ```

3. Configure the `.env` variables:

   ```bash
    LOG_VERBOSITY=INFO
    APP_NAME=bakky
    APP_VERSION=0.0.1
    DEBUG=True
    API_PREFIX=/api/v1
    SECRET_KEY=your-secret-key
   ```

4. Install the dependencies with python uv: `uv sync`
5. Run the project: you have different method to use
   1. Use the command `uvicorn main:app --reload` to run the project manually with uvicorn
   2. Use the bash script: `./scripts/launch.sh`
   3. User Makefile: `make run`
   4. Use vscode debugger configured inside the repo
6. Launch docker-compose to create the backend: `make launch`

## Progress

List of features that I'm working on and things that I want to implement in this project.

- [x] project setup with uv
- [x] Makefile
- [x] Project structure
- [x] utils
- [x] config
- [x] vscode settings and debugger
- [x] gitlab and github templates
- [x] pytest configuration
- [x] docker-compose
- [x] devcontainer
- [x] postgres with different mode (ORM, raw, yaml)
- [x] mongo
- [ ] redis
- [ ] file (parquet, delta)
- [ ] models
- [ ] schemas
- [ ] routes
