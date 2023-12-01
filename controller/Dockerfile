FROM python:latest

WORKDIR /app
COPY controller.py .

RUN pip install kubernetes

# Run the proxy on container startup.
CMD [ "python3", "controller.py" ]
