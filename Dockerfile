FROM python:3.9.2-slim-buster

RUN apt-get update && apt-get upgrade -y && apt-get install -y procps


COPY . .

COPY requirements.txt .
RUN pip install -r requirements.txt

ENV IS_CONTAINER=True

CMD ["python", "app.py"]




