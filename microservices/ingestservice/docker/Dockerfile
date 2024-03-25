FROM python:3.10

COPY requirements.txt requirements.txt
RUN apt-get update && apt-get install -y \
    bison \
    flex \
    libtool \
    make \
    automake \
    autoconf

RUN pip install wheel \
    pip install --no-cache-dir --upgrade -r requirements.txt

COPY src/main.py src/main.py
COPY src/preprocess_data.py src/preprocess_data.py
COPY src/oss_accessor.py src/oss_accessor.py
COPY dto/recoexplorer_item.py dto/recoexplorer_item.py

COPY config/config.yaml config.yaml

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "80"]