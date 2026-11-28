FROM mcr.microsoft.com/playwright/python:v1.58.0-noble

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN python -m pip install --no-cache-dir playwright==1.58.0 \
    && install -d -o pwuser -g pwuser /input /output
COPY --chown=pwuser:pwuser browser_runner.py /opt/ui-eval/browser_runner.py

USER pwuser
WORKDIR /opt/ui-eval
