# Context must contain source/ verified against the signed v1.6.5 commit.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim@sha256:e5b65587bce7de595f299855d7385fe7fca39b8a74baa261ba1b7147afa78e58 AS frozen
WORKDIR /src
COPY source/ /src/
ENV UV_LINK_MODE=copy UV_COMPILE_BYTECODE=1 UV_PYTHON_DOWNLOADS=never
RUN uv sync --frozen --no-dev --no-editable --extra gliner --extra postgres-binary

# Copy only the upstream-pinned JSON extension binaries, never its Python venv.
FROM docker.io/cognee/cognee:1.6.5@sha256:29427e968f8b273db0bb7b037a7bb119d7695d960f73a59d649f00c5111a85bd AS extensions
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim@sha256:e5b65587bce7de595f299855d7385fe7fca39b8a74baa261ba1b7147afa78e58
WORKDIR /src
COPY --from=frozen /src /src
COPY --from=extensions /app/cognee_db_workers/ladybug_extensions/ /src/cognee_db_workers/ladybug_extensions/
RUN groupadd --gid 1000 cognee && useradd --uid 1000 --gid 1000 --no-create-home cognee && mkdir -p /cognee-storage && chown 1000:1000 /cognee-storage /src && chmod 0555 /src/entrypoint.sh
ENV PATH="/src/.venv/bin:/usr/local/bin:/usr/bin:/bin" PYTHONPATH=/src HOME=/src PYTHONUNBUFFERED=1
LABEL org.opencontainers.image.source="https://github.com/topoteretes/cognee" org.opencontainers.image.version="1.6.5" org.opencontainers.image.revision="37f788bd287750e10d7610173e5332b3843f6ebd"
USER 1000:1000
RUN --network=none python -c "from cognee_db_workers._kuzu_helpers import install_json_extension_local; install_json_extension_local(buffer_pool_size=268435456)"
ENTRYPOINT ["/src/entrypoint.sh"]
