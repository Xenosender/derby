FROM tensorflow/tensorflow:1.12.0-gpu-py3

RUN apt-get update && apt-get install -y \
    wget \
    libsm6 \
    libxrender1 \
    libxext6

RUN mkdir /src
COPY . /src/
RUN cd /src && pip3 install -r requirements.txt
RUN cd /src/model && ./download_all_models.sh

WORKDIR /src
ENTRYPOINT ["python3", "aws_interface.py"]
