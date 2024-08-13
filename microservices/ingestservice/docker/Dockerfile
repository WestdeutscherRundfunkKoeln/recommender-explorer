FROM python:3.10-slim

COPY requirements.txt requirements.txt
RUN apt-get update && apt-get install -y \
    bison \
    flex \
    libtool \
    make \
    automake \
    autoconf

RUN python -m pip install wheel && \
    python -m pip install --no-cache-dir --upgrade -r requirements.txt

COPY src/main.py src/main.py
COPY src/preprocess_data.py src/preprocess_data.py
COPY src/models.py src/models.py
COPY src/task_status.py src/task_status.py
COPY dto/recoexplorer_item.py dto/recoexplorer_item.py

COPY config/config.yaml config.yaml

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "80"]
