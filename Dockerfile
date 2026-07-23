# syntax=docker/dockerfile:1

FROM node:22-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build


FROM python:3.14-slim AS backend
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        chromium \
        chromium-driver \
        fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# guardrails-grhub-detect-pii and guardrails-grhub-toxic-language are hosted on
# Guardrails' private, token-gated package index (pypi.guardrailsai.com), not
# public PyPI - install them here via a BuildKit secret so the token is never
# written into an image layer. requirements.txt below then sees these two as
# already satisfied. (Mirrors what `guardrails hub install` does internally.)
RUN --mount=type=secret,id=guardrails_token \
    pip install --no-cache-dir \
        --index-url "https://__token__:$(cat /run/secrets/guardrails_token)@pypi.guardrailsai.com/simple" \
        --extra-index-url https://pypi.org/simple \
        guardrails-grhub-detect-pii==0.0.6 guardrails-grhub-toxic-language==0.0.2

RUN pip install --no-cache-dir -r requirements.txt

# The `guardrails.hub` dynamic-import shim resolves via .guardrails/hub_registry.json
# in the current working directory - not a secret, just static metadata recording
# that toxic_language is installed, so it's baked in directly.
COPY docker/hub_registry.json .guardrails/hub_registry.json

# Without a ~/.guardrailsrc, guardrails-ai defaults use_remote_inferencing=True and
# ToxicLanguage calls a hosted inference API instead of running the ALBERT model
# warmed up below - matching local dev's rc file, not a secret (just settings, no
# token), so it's baked in directly rather than routed through the build secret.
COPY docker/guardrailsrc /root/.guardrailsrc

# Warm up model/data downloads at build time so the first request doesn't pay for
# them: the ALBERT weights behind ToxicLanguage, and NLTK punkt data + presidio's
# AnalyzerEngine/AnonymizerEngine (which loads the en_core_web_lg spaCy model
# installed above via requirements.txt) behind DetectPII.
RUN python -c "from guardrails.hub import ToxicLanguage; ToxicLanguage()"
RUN python -c "import importlib.util as u, pathlib; p = pathlib.Path(u.find_spec('guardrails_grhub_detect_pii').origin).parent / 'post-install.py'; exec(p.read_text())"

COPY src/ ./src
COPY app.py ./
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

ENV CHROME_BIN=/usr/bin/chromium \
    SCRAPER_HEADLESS=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
