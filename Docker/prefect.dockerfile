FROM prefecthq/prefect:3.2.2-python3.12

# Install libraries
RUN DEBIAN_FRONTEND=noninteractive apt update && apt install -y --no-install-recommends curl ca-certificates \
    libpq-dev gcc wget gnupg2 openssh-client git make build-essential \
    libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev \
    llvm libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \
    libffi-dev liblzma-dev unzip lsof

# # Install aws cli
# RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
#     && unzip awscliv2.zip \
#     && ./aws/install

# Install UV
ARG UV_VERSION="0.6.14"
ENV UV_VERSION=${UV_VERSION}
COPY --from=ghcr.io/astral-sh/uv:${UV_VERSION} /uv /uvx /bin/

# COPY ./scripts/launch_prefect.sh ./scripts/launch_prefect.sh
# COPY ./Docker/prefect_server.dockerfile ./Docker/prefect_server.dockerfile
# COPY ./Docker/prefect_worker.dockerfile ./Docker/prefect_worker.dockerfile
# COPY ./config/prefect.yaml ./config/prefect.yaml

EXPOSE 4200
