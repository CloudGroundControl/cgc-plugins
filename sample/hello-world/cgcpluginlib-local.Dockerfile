FROM python:3.10-slim-bullseye

RUN apt-get update
RUN apt-get install -y --no-install-recommends gcc pciutils libgl1 ffmpeg libsm6 libxext6 g++
RUN apt-get clean && rm -rf /var/lib/apt/lists/* 

COPY requirements.txt /requirements.txt

RUN pip install --no-cache-dir wheel
RUN pip install --no-cache-dir -r requirements.txt

COPY cgcpluginlib-0.0.6-py3-none-any.whl /cgcpluginlib-0.0.6-py3-none-any.whl
RUN pip install cgcpluginlib-0.0.6-py3-none-any.whl

# Required for PIL ImageFont to work
COPY arial.ttf /arial.ttf

COPY main.py /main.py
COPY start-app.sh /start-app.sh

# required for python logs to show
ENV PYTHONUNBUFFERED=1

