
FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y libglib2.0-0 libsm6 libxext6 libxrender-dev && \
    pip install flask requests pillow pandas

WORKDIR /app
COPY . /app

CMD ["python", "app.py"]
