#!/bin/bash
set -e

ETAG_PATH="/tmp/etag.txt"

# Check if etag file exists and has content
if [ -f "$ETAG_PATH" ] && [ -s "$ETAG_PATH" ]; then
    echo "Etag found, running minutely changes..."
    ODF_ETAG=$(cat "$ETAG_PATH")

    # Run the minutely changes container
    docker-compose run --rm \
        -e ODF_ETAG="$ODF_ETAG" \
        -e ODF_NEW_ETAG_PATH="$ETAG_PATH" \
        osm-minutely-changes
else
    echo "No etag found, running initial PBF ingestion..."

    # Run the pbf-to-csv container
    docker-compose run --rm \
        -e ODF_NEW_ETAG_PATH="$ETAG_PATH" \
        osm-pbf-to-csv
fi
