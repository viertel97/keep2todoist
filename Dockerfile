


# Create a venv using the larger base image (which contains gcc).
FROM python:3.10-bullseye AS builder
RUN python3 -m venv /venv
COPY requirements.txt /requirements.txt
RUN /venv/bin/pip3 install --no-cache-dir -r /requirements.txt

# Copy the venv to a fresh "slim" image.
FROM python:3.10-slim-bullseye
RUN apt-get update && apt-get upgrade -y && apt-get install -y procps

COPY --from=builder /venv /venv
WORKDIR /app
COPY . .
ENV IS_CONTAINER=True

CMD ["/venv/bin/python3", "app.py"]



