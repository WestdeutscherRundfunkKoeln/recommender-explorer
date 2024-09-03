FROM python:3.11-slim

COPY requirements.txt requirements.txt

RUN python -m pip install wheel && \
    python -m pip install --no-cache-dir --upgrade -r requirements.txt

COPY src src

COPY config/config.yaml config.yaml

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "80"]
