FROM golang:1.26.8-alpine3.24@sha256:ce864e7223ac17b1775e6fd0b4c0db580c2eb50e7953a427916379e4b92a1628 AS actionlint

ARG ACTIONLINT_VERSION=1.7.12
RUN CGO_ENABLED=0 go install github.com/rhysd/actionlint/cmd/actionlint@v${ACTIONLINT_VERSION}

FROM python:3.12.14-slim-trixie@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea

RUN apt-get update && apt-get upgrade --yes && rm -rf /var/lib/apt/lists/*

ARG ZIZMOR_VERSION=1.26.1

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY --from=actionlint /go/bin/actionlint /usr/local/bin/actionlint
RUN pip install --no-cache-dir "zizmor==${ZIZMOR_VERSION}"

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
