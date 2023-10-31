FROM golang:1.21.3

WORKDIR /app
# Copy the proxy code to the container.
COPY main.go .
COPY go.mod .
RUN go mod tidy

# Run the proxy on container startup.
ENTRYPOINT [ "go" ]
CMD [ "run", "main.go" ]

# Expose the proxy port.
EXPOSE 8000