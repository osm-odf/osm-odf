FROM alpine:3.19

WORKDIR /app

# Install bash for script execution
RUN apk add --no-cache bash docker-cli-compose

# Copy the script
COPY check-etag.sh /app/
RUN chmod +x /app/check-etag.sh

# Set the script as the entrypoint
ENTRYPOINT ["/app/check-etag.sh"]
