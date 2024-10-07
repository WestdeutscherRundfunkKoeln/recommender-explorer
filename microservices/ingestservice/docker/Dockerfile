FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    bison \
    flex \
    libtool \
    make \
    automake \
    autoconf \
    curl

COPY requirements.txt requirements.txt

RUN python -m pip install wheel && \
    python -m pip install --no-cache-dir --upgrade -r requirements.txt

COPY src src
COPY dto/recoexplorer_item.py dto/recoexplorer_item.py

COPY config/config.yaml config.yaml

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "80"]
