FROM alpine:latest

RUN apk add --no-cache docker

WORKDIR /app
COPY osm-ingester.sh /app/
RUN chmod +x /app/osm-ingester.sh

ENTRYPOINT ["/app/osm-ingester.sh"]
