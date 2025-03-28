FROM alpine:latest

RUN apk add --no-cache docker

WORKDIR /app
COPY osm-ingester.sh . 
RUN ls -la /app && chmod +x osm-ingester.sh
RUN chmod +x osm-ingester.sh

ENTRYPOINT ["/bin/sh", "/app/osm-ingester.sh"]