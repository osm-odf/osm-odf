#!/bin/bash
set -e

export ODF_NEW_ETAG_PATH="/tmp/etag.txt"

run_minutely_updates() {

    # Set environment variable
    export VERBOSE=0
    export NODES=0
    export WAYS=0
    export RELATIONS=0
    export TAGS=0

    python osm-minutely-changes/consumer.py "$ODF_ETAG" "$ODF_NEW_ETAG_PATH"
}

run_osm_pbf_seed() {

    java -jar /app/app.jar /input/berlin/berlin-latest-internal.osm.pbf "$ODF_NEW_ETAG_PATH"
}

echo "Checking ODF_ETAG environment variable..."

# Set ODF_ETAG to content of file at ODF_NEW_ETAG_PATH if the file exists
if [ -f "$ODF_NEW_ETAG_PATH" ]; then
    export ODF_ETAG=$(cat "$ODF_NEW_ETAG_PATH")
    echo "ODF_ETAG set to: $ODF_ETAG"
else
    echo "File $ODF_NEW_ETAG_PATH does not exist, ODF_ETAG not set"
fi

if [ -z "$ODF_ETAG" ]; then
    echo "Running osm-pbf-to-csv..."
    run_osm_pbf_seed
    echo "Done"
else
    echo "Running osm-minutely-changes..."
    run_minutely_updates
fi

echo "ODF_ETAG = $(cat /tmp/etag.txt)"
