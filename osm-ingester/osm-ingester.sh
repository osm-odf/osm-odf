#!/bin/bash
set -e

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
    exec docker run --rm osm-pbf-to-csv-image /input/berlin/berlin-latest-internal.osm.pbf "$ODF_NEW_ETAG_PATH"
    echo "Done"
else
    echo "Running osm-minutely-changes..."
    exec docker run --rm osm-minutely-changes-image "$ODF_ETAG" "$ODF_NEW_ETAG_PATH"
    echo "Done"
fi

