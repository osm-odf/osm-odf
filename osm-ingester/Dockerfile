
# BUILD

FROM gradle:8.10-jdk17 AS build

WORKDIR /app

# Prepare to build
COPY osm-pbf-to-csv/*.kts .
COPY osm-pbf-to-csv/*.properties .
COPY osm-pbf-to-csv/gradlew .
COPY osm-pbf-to-csv/gradlew.bat .
COPY osm-pbf-to-csv/gradle ./gradle
COPY osm-pbf-to-csv/src ./src

# Build the project
RUN ./gradlew build

# Install Berlin data
RUN mkdir /input
RUN mkdir /output
COPY ../data/berlin/berlin-latest-internal.osm.pbf /input


# RUN

FROM openjdk:17-jdk-slim

ENV ODF_ETAG=""
ENV ODF_NEW_ETAG_PATH="/tmp/etag.txt"

# Copy built artifacts from build stage
COPY --from=build /app/build/libs/*.jar ./app.jar

# Install dependencies (curl, bash, gradle, python, and pip)
RUN apt-get update && \
    apt-get install -y \
    curl \
    bash \
    unzip \
    python3 \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install python script
COPY osm-minutely-changes/requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Set up ingester script
WORKDIR /app
COPY osm-ingester.sh .
RUN ls -la /app && chmod +x osm-ingester.sh
RUN chmod +x osm-ingester.sh

ENTRYPOINT ["/bin/sh", "/app/osm-ingester.sh"]
