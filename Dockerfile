FROM python:3.9.5-alpine
RUN pip install --upgrade pip

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python3", "./app.py"]