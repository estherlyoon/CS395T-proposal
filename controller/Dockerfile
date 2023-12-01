FROM python:latest
RUN pip install kubernetes prometheus-api-client

WORKDIR /app
COPY controller.py .


# Run the proxy on container startup.
CMD [ "python3", "controller.py" ]
