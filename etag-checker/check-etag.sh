#!/bin/bash
set -e

echo "Checking ODF_ETAG environment variable..."

export ODF_NEW_ETAG_PATH="/tmp/etag.txt"

# Set ODF_ETAG to content of file at ODF_NEW_ETAG_PATH if the file exists
if [ -f "$ODF_NEW_ETAG_PATH" ]; then
    export ODF_ETAG=$(cat "$ODF_NEW_ETAG_PATH")
    echo "ODF_ETAG set to: $ODF_ETAG"
else
    echo "File $ODF_NEW_ETAG_PATH does not exist, ODF_ETAG not set"
fi

if [ -z "$ODF_ETAG" ]; then
    echo "ODF_ETAG is empty, running osm-pbf-to-csv with ODF_NEW_ETAG_PATH..."

    # Determine the command to run
    JAVA_CMD="java -jar /app/app.jar /input/berlin/berlin-latest-internal.osm.pbf $ODF_NEW_ETAG_PATH"

    # Execute the Java command directly if we're already in the container
    if [ -f "/app/app.jar" ]; then
        echo "Running Java command directly: $JAVA_CMD"
        eval "$JAVA_CMD"
    else
        # Use docker-compose to run the service with the custom command
        echo "Running via docker-compose: $JAVA_CMD"
        # Make sure to specify the path to your docker-compose.yml file if needed
        docker compose -f ./docker-compose.yml run --rm \
            osm-pbf-to-csv \
            sh -c "$JAVA_CMD"
    fi

    echo "osm-pbf-to-csv execution completed."
else
    echo "ODF_ETAG is not empty, running osm-minutely-changes..."

    # Check if we're in a container or need to use docker-compose
    if [ -f "/app/app.jar" ]; then
        # We're already in the container, run the appropriate command
        echo "Running minutely changes directly"
        # Add your direct command here
    else
        # Pass ODF_ETAG and ODF_NEW_ETAG_PATH to the osm-minutely-changes container
        # Make sure to specify the path to your docker-compose.yml file if needed
        docker compose -f ./docker-compose.yml run --rm \
            -e ODF_ETAG="$ODF_ETAG" \
            -e ODF_NEW_ETAG_PATH="$ODF_NEW_ETAG_PATH" \
            osm-minutely-changes
    fi

    echo "osm-minutely-changes execution completed."
fi
