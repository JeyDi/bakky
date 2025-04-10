# Reference:
# * https://hynek.me/articles/docker-uv/

ARG UV_VERSION="0.6.14"
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

FROM python:3.12.9-slim-bookworm

# Metadata
LABEL name="Python 3.12.9"
LABEL maintainer="JeyDi"

ARG UV_PYTHON=python3.12

# Install requirements
RUN DEBIAN_FRONTEND=noninteractive apt update && apt install -y --no-install-recommends curl ca-certificates \
    libpq-dev gcc wget gnupg2 openssh-client git make build-essential \
    libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev \
    llvm libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \
    libffi-dev liblzma-dev unzip

# Install aws cli
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install

### Start build prep

COPY --from=uv /uv /bin/uv

# - Silence uv complaining about not being able to use hard links,
# - tell uv to byte-compile packages for faster application startups,
# - prevent uv from accidentally downloading isolated Python builds,
# - pick a Python version to use for the uv command.
# - add the cargo binary directory to the PATH
ENV \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=${UV_PYTHON} \
    PATH="/root/.cargo/bin/:$PATH"

