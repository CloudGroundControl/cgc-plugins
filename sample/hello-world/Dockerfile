FROM python:3.10-slim-bullseye

RUN apt-get update
RUN apt-get install -y --no-install-recommends gcc pciutils libgl1 ffmpeg libsm6 libxext6 g++
RUN apt-get clean && rm -rf /var/lib/apt/lists/* 

COPY requirements.txt /requirements.txt

RUN pip install --no-cache-dir wheel
RUN pip install --no-cache-dir -r requirements.txt

# install cgcpluginlib from test pypi, install deps manually as they don't get installed from test pypi
RUN pip install --no-cache-dir watchdog==3.0.0
RUN pip install --no-cache-dir argparse==1.4.0
RUN pip install --no-cache-dir --no-deps -i https://test.pypi.org/simple/ cgcpluginlib==0.0.6

# Required for PIL ImageFont to work
COPY arial.ttf /arial.ttf

COPY main.py /main.py
COPY start-app.sh /start-app.sh

# required for python logs to show
ENV PYTHONUNBUFFERED=1
