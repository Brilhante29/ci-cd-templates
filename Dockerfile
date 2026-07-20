FROM python:3.12-slim

ARG ACTIONLINT_VERSION=1.7.12
ARG ZIZMOR_VERSION=1.26.1

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install --no-install-recommends --yes ca-certificates curl \
    && case "$(dpkg --print-architecture)" in \
         amd64) actionlint_arch="amd64" ;; \
         arm64) actionlint_arch="arm64" ;; \
         *) echo "unsupported architecture" >&2; exit 1 ;; \
       esac \
    && curl --fail --silent --show-error --location \
       "https://github.com/rhysd/actionlint/releases/download/v${ACTIONLINT_VERSION}/actionlint_${ACTIONLINT_VERSION}_linux_${actionlint_arch}.tar.gz" \
       | tar --extract --gzip --file=- --directory=/usr/local/bin actionlint \
    && pip install --no-cache-dir "zizmor==${ZIZMOR_VERSION}" \
    && apt-get purge --auto-remove --yes curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md REFERENCES.md ./
COPY src ./src
COPY tests ./tests
COPY benchmarks ./benchmarks
COPY .github ./.github
COPY sdd ./sdd
COPY project.yaml ./project.yaml
COPY tools ./tools

RUN pip install --no-cache-dir .

ENTRYPOINT ["python", "-m", "ci_guardrails"]
CMD ["scan", ".github/workflows", "--deterministic"]
