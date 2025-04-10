
# BUILD

FROM gradle:8.10-jdk17 AS build

RUN apt-get update && \
    apt-get install -y \
    gcc \
    curl

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

# RUN

FROM openjdk:17-jdk-slim

RUN apt-get update && \
    apt-get install -y \
    gcc \
    curl

ENV ODF_ETAG=""
ENV ODF_NEW_ETAG_PATH="/tmp/etag.txt"

# ENV PATH="$HOME/.cargo/bin:${PATH}"

RUN curl https://sh.rustup.rs -sSf | sh -s -- -y && \
    . $HOME/.cargo/env && \
    cargo install --root /usr/local osm-cli


# Install Berlin data
RUN mkdir -p /input/berlin
RUN mkdir -p /output/berlin
COPY ../data/berlin/berlin-latest-internal.osm.pbf /input/berlin

# Copy built artifacts from build stage
WORKDIR /app
COPY --from=build /app/build/libs/*.jar ./app.jar
# COPY --from=build /usr/local/bin/osm /usr/local/bin/

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
WORKDIR /app
COPY osm-minutely-changes/* .
RUN pip3 install --no-cache-dir -r requirements.txt

# Set up ingester script
WORKDIR /app
COPY osm-ingester.sh .
RUN ls -la /app && chmod +x osm-ingester.sh
RUN chmod +x osm-ingester.sh

ENTRYPOINT ["/bin/sh", "/app/osm-ingester.sh"]
