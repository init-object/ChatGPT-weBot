FROM python:3.9-slim-buster
RUN apk add --no-cache python3-dev libffi-dev gcc musl-dev make libevent-dev
WORKDIR /chatgpt-webot
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt 
COPY . .
CMD [ "python", "main.py"]
