FROM python:3.10-slim

COPY requirements.txt requirements.txt

RUN python -m pip install wheel &&\
    python -m pip install --no-cache-dir --upgrade -r requirements.txt

COPY src/main.py src/main.py
COPY src/embed_text.py src/embed_text.py
COPY dto/embed_data.py dto/embed_data.py

COPY config/config.yaml config.yaml

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "80"]
