FROM python:3.13-slim AS oracle

COPY oracle_stub.py /oracle_stub.py
ENV ORACLE_BIND=0.0.0.0
ENV ORACLE_PORT=80
EXPOSE 80
CMD ["python", "/oracle_stub.py"]

FROM python:3.13-slim AS loom

WORKDIR /app

COPY src-v1.9.0/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src-v1.9.0/backend/app/ ./app/
COPY src-v1.9.0/backend/etc/models.json src-v1.9.0/backend/etc/runtime_pricing.json src-v1.9.0/backend/etc/providers.json ./etc/
COPY lab_patch.py sitecustomize.py /tmp/lab-py/
RUN python -c "import pathlib, shutil, site; dest = pathlib.Path(site.getsitepackages()[0]); shutil.copy('/tmp/lab-py/lab_patch.py', dest); shutil.copy('/tmp/lab-py/sitecustomize.py', dest)"
COPY poc.py /lab/poc.py

ENV PYTHONPATH=/app
ENV LOOM_DATABASE_URL=sqlite:////tmp/loom.db
RUN groupadd --system appuser \
    && useradd --system --gid appuser --home-dir /tmp appuser \
    && chown -R appuser:appuser /app /lab
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
