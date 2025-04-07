#!/bin/bash
set -e

#
# Reads any ODF "ETAG" value stored in the file at the given path
#
# Arguments:
#    path - Path to the file to read from
#
# Returns:
#    The ODF "ETAG" value read from the given path, or an empty string if the file doesn't exist
#
read_etag() {

    local path="$1"
    local etag=""

    # If path exists,
    if [ -f "$path" ]; then

        # read the contents of that file,
        etag=$(cat "$path")

    fi

    echo "$etag"
}

#
# Convert the given Unix timestamp to an Overpass augmented diff sequence number
#
# Arguments:
#    timestamp - Unix timestamp value in milliseconds since the start of the Unix epoch
#
# Returns:
#    The Overpass augmented diff sequence number identifying the first minutely
#    update that occurred after the given timestamp
#
timestamp_to_overpass_sequence_number() {

    local timestamp="$1"

    local since=$(date -r "$timestamp")
    local sequence_number=$(osm replication minute --since "$since" | head -n 1 | awk '{print $1}')

    echo "$sequence_number"
}

#
# Outputs CSV data to update the Kamu Node data store. The output is the data from the given
# Overpass augmented diff, as specified by its sequence number.
#
# Arguments:
#    sequence_number - The sequence number of the minutely augmented diff to download
#    sequence_number_output_path - The path where the next sequence number should be written
#
update() {

    local sequence_number="$1"
    local sequence_number_output_path="$2"

    # Set environment variables
    export VERBOSE=0
    export NODES=0
    export WAYS=0
    export RELATIONS=0
    export TAGS=0

    echo "Downloading minutely augmented diff #$sequence_number from Overpass..."
    python osm-minutely-changes/consumer.py "$sequence_number" "$sequence_number_output_path"
    echo "Next sequence number was written to $sequence_number_output_path"
    echo "Done"
}

#
# Outputs CSV files given an input OSM PBF file. The output files are written alongside to the
# input file. The maximum Unix timestamp value found in the input is written to the given output path.
#
# Arguments:
#    kamu_dataset - The name of the Kamu dataset to create
#    kamu_dataset_path - The path to the YAML file that defines the Kamu dataset
#    osm_pbf_input_path - The path to the OSM PBF file to read
#    timestamp_output_path - The path where the maximum timestamp should be written
#
initialize() {

    local kamu_dataset="$1"
    local kamu_dataset_path="$2"
    local osm_pbf_input_path="$3"
    local timestamp_output_path="$4"

    # Run Kotlin JVM application to extract CSV files from OSM PBF file. The first parameter is a
    # path to an OSM PBF input file. The second parameter is a path to a file where the application
    # should write the maximum UNIX timestamp found in the OSM PBF file.
    echo "Converting $osm_pbf_input_path to CSV files..."
    java -jar /app/app.jar "$osm_pbf_input_path" "$timestamp_output_path"
    local maximum_timestamp=$(cat "$timestamp_output_path")
    echo "Maximum timestamp ($maximum_timestamp) was written to $timestamp_output_path"
    echo "Done"

    # Now, initialize Kamu workspace, add the given dataset and pull the data into Kamu
    echo "Adding initial snapshot to Kamu"
    kamu init
    kamu add "$kamu_dataset_path"
    kamu pull "$kamu_dataset"
    echo "Done"
}

# Kamu Node will set these environment variables
export ODF_NEW_ETAG_PATH="/tmp/etag.txt"
export ODF_ETAG=$(read_etag "$ODF_NEW_ETAG_PATH")

#
# Run ingestion process. If
#
main() {

    # Name of Kamu dataset
    local kamu_dataset="berlin"

    # Path to Kamu dataset YAML definition
    local kamu_dataset_path="/input/berlin/berlin.yaml"

    # Path to OSM PBF file to use as initial starting point if ingestion is being initialized
    local osm_pbf_snapshot_path="/input/berlin/berlin-latest-internal.osm.pbf"

    #-----------------------------------------------------------------------

    # Show initial environment variables,
    echo "ODF_ETAG => $ODF_ETAG"
    echo "ODF_NEW_ETAG_PATH => $ODF_NEW_ETAG_PATH"

    # and if there is no ODF_ETAG value,
    local etag_type
    if [ -z "$etag" ]; then

        # run the OSM PBF to CSV converter Kotlin app to extract initial CSV files from the initial
        # OSM PBF snapshot file and import them into Kamu Node,
        initialize "$kamu_dataset" "$kamu_dataset_path" "$osm_pbf_snapshot_path" "$ODF_NEW_ETAG_PATH"

        # and note that the value output to the etag path is a timestamp,
        etag_type="timestamp"

    else

        # otherwise, the etag is a Unix timestamp,
        local timestamp="$etag"

        # so we can convert to an Overpass augmented diff sequence number,
        local sequence_number=timestamp_to_overpass_sequence_number "$etag"

        # which we can use to get the next minutely update from Overpass
        # (this process writes the next sequence number to the etag path).
        update "$sequence_number" "$ODF_NEW_ETAG_PATH"

        # Make a note that the etag file now contains a sequence number.
        etag_type="sequence number"

    fi

    # Show the new ETAG value written by initialize (will be a Unix timestamp) or update (will be a
    local new_etag=$(read_etag "$ODF_NEW_ETAG_PATH")
    echo "New ODF_ETAG => $new_etag ($etag_type)"
}

main
