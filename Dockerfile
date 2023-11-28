FROM python:3.9.2-slim-buster

COPY . .

COPY requirements.txt .
RUN pip install -r requirements.txt

ENV IS_CONTAINER=True

CMD ["python", "app.py"]




