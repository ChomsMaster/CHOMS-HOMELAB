FROM python:3.13-alpine@sha256:540c7d91f98ff6880174c40e99067bf5941eb54d818a7a5e094d188b196a934d

WORKDIR /app
COPY monitor.py healthcheck.py config.json ./
RUN chmod 0555 /app/monitor.py /app/healthcheck.py && chmod 0444 /app/config.json
USER 1000:1000
ENTRYPOINT ["python3", "/app/monitor.py"]
