FROM python:3.12.13-slim@sha256:423ed6ab25b1921a477529254bfeeabf5855151dc2c3141699a1bfc852199fbf

ARG ACTIONLINT_VERSION=1.7.12
ARG ACTIONLINT_AMD64_SHA256=8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8
ARG ACTIONLINT_ARM64_SHA256=325e971b6ba9bfa504672e29be93c24981eeb1c07576d730e9f7c8805afff0c6
ARG ZIZMOR_VERSION=1.26.1

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install --no-install-recommends --yes ca-certificates curl \
    && case "$(dpkg --print-architecture)" in \
         amd64) actionlint_arch="amd64"; actionlint_sha="${ACTIONLINT_AMD64_SHA256}" ;; \
         arm64) actionlint_arch="arm64"; actionlint_sha="${ACTIONLINT_ARM64_SHA256}" ;; \
         *) echo "unsupported architecture" >&2; exit 1 ;; \
       esac \
    && curl --fail --silent --show-error --location \
       --output /tmp/actionlint.tar.gz \
       "https://github.com/rhysd/actionlint/releases/download/v${ACTIONLINT_VERSION}/actionlint_${ACTIONLINT_VERSION}_linux_${actionlint_arch}.tar.gz" \
    && echo "${actionlint_sha}  /tmp/actionlint.tar.gz" | sha256sum --check --strict \
    && tar --extract --gzip --file=/tmp/actionlint.tar.gz --directory=/usr/local/bin actionlint \
    && rm /tmp/actionlint.tar.gz \
    && pip install --no-cache-dir "zizmor==${ZIZMOR_VERSION}" \
    && apt-get purge --auto-remove --yes curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml constraints.lock README.md REFERENCES.md LICENSE ./
COPY src ./src
COPY tests ./tests
COPY benchmarks ./benchmarks
COPY .github ./.github
COPY sdd ./sdd
COPY project.yaml ./project.yaml
COPY tools ./tools
COPY .portfolio/contracts/benchmark-result-v2.schema.json ./.portfolio/contracts/benchmark-result-v2.schema.json
# validate --strict requires Dockerfile in the validated root and scans its
# contents for credential material, so the image must carry it.
COPY Dockerfile ./Dockerfile

RUN PIP_CONSTRAINT=/app/constraints.lock pip install --no-cache-dir ".[dev]" \
    && useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app

USER appuser

ENTRYPOINT ["python", "-m", "ci_guardrails"]
CMD ["scan", ".github/workflows", "--deterministic", "--fail-on", "any"]
