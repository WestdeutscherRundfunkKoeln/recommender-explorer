FROM python:3.11-slim

COPY requirements.txt requirements.txt

RUN python -m pip install wheel && \
    python -m pip install --no-cache-dir --upgrade -r requirements.txt

COPY src/main.py src/main.py
COPY src/models.py src/models.py
COPY src/oss_accessor.py src/oss_accessor.py

COPY config/config.yaml config.yaml

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "80"]
