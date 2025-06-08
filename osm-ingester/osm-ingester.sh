#!/bin/bash
set -e

VERBOSE=1

say() {

    if [ "$VERBOSE" -eq 1 ]; then
        echo "$1"
    fi
}

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

    say "$etag"
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
timestamp_to_sequence_number() {
    local timestamp="$1"
    say "timestamp=$timestamp" >&2
    utc_date=$(python3 -c "import time; print(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime($timestamp/1000)))")
    say "utc_date=$utc_date" >&2
    local seconds_since_epoch
    seconds_since_epoch=$(date --date="$utc_date" +%s)
    local sequence_number=$(( (seconds_since_epoch + 59) / 60 - 22457216 ))
    say "$sequence_number"
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

    say "Downloading minutely augmented diff #$sequence_number from Overpass..."
    python3 /app/consumer.py "$sequence_number" "$sequence_number_output_path"
    say "Next sequence number was written to $sequence_number_output_path"
    say "Done"
}

#
# Shows the state of each environment variable that controls output
#
show_environment_variables() {

    say "NODES = $NODES"
    say "WAYS = $WAYS"
    say "RELATIONS = $RELATIONS"
    say "TAGS = $TAGS"
    say "MEMBERS = $MEMBERS"
}

#
# Ensures that one and only one environment variable that controls output is set
#
check_environment_variables() {

    local variables=0

    if [ -n "$NODES" ]; then
        variables=$((variables + 1))
    fi
    if [ -n "$WAYS" ]; then
        variables=$((variables + 1))
    fi
    if [ -n "$RELATIONS" ]; then
        variables=$((variables + 1))
    fi
    if [ -n "$TAGS" ]; then
        variables=$((variables + 1))
    fi
    if [ -n "$MEMBERS" ]; then
        variables=$((variables + 1))
    fi

    if [ "$variables" -eq 0 ]; then
        say "Error: None of the environment variables (NODES, WAYS, RELATIONS, TAGS, MEMBERS) are set. Please set at least one." >&2
        exit 1
    fi

    if [ "$variables" -gt 1 ]; then
        say "Error: More than one environment variable (NODES, WAYS, RELATIONS, TAGS, MEMBERS) is set. Please set only one." >&2
        exit 1
    fi
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

    local osm_pbf_input_path="$1"
    local timestamp_output_path="$2"

    # Run Kotlin JVM application to extract CSV files from OSM PBF file. The first parameter is a
    # path to an OSM PBF input file. The second parameter is a path to a file where the application
    # should write the maximum UNIX timestamp found in the OSM PBF file.
    say "Converting $osm_pbf_input_path to CSV files..."
    java -jar /app/app.jar "$osm_pbf_input_path" "$timestamp_output_path"
    local maximum_timestamp=$(cat "$timestamp_output_path")
    say "Maximum timestamp ($maximum_timestamp) was written to $timestamp_output_path"
    say "Done"
}

# Kamu Node will set these environment variables
export ODF_NEW_ETAG_PATH="/tmp/etag.txt"
export ODF_ETAG=$(read_etag "$ODF_NEW_ETAG_PATH")

show_environment_variables
check_environment_variables

#
# Run ingestion process. If
#
main() {

    # Path to OSM PBF file to use as initial starting point if ingestion is being initialized
    local osm_pbf_snapshot_path="/input/berlin/berlin-latest-internal.osm.pbf"

    #-----------------------------------------------------------------------

    # Show initial environment variables,
    say "ODF_ETAG => $ODF_ETAG"
    say "ODF_NEW_ETAG_PATH => $ODF_NEW_ETAG_PATH"

    # and if ODF_ETAG is empty,
    local etag_type
    if [ -z "$ODF_ETAG" ]; then

        # run the OSM PBF to CSV converter Kotlin app on the snapshot to get the initial map data,
        say "Initializing from snapshot..."
        initialize "$osm_pbf_snapshot_path" "$ODF_NEW_ETAG_PATH"

        # (noting that the value output to the etag path is a timestamp)
        etag_type="timestamp"

    else

        local sequence_number

        # otherwise, if ODF_ETAG < 0,
        if [ "$ODF_ETAG" -lt 0 ]; then

            # it's a Unix timestamp written out by initialize() when the PBF snapshot was read,
            local timestamp="${ODF_ETAG#-}"

            # so we need to convert the timestamp to an Overpass augmented diff sequence number,
            sequence_number=$(timestamp_to_sequence_number "$timestamp")

        else

            # but if ODF_ETA >= 0, then ODF_ETAG is the sequence number.
            sequence_number="$ODF_ETAG"

        fi

        # Use the sequence number to get the next minutely update from Overpass
        # (this process writes the next sequence number to the etag path).
        update "$sequence_number" "$ODF_NEW_ETAG_PATH"

        # Make a note that the etag file now contains a sequence number.
        etag_type="sequence number"

    fi

    # Show the new ETAG value written by initialize (will be a Unix timestamp) or update (will be a
    local new_etag=$(read_etag "$ODF_NEW_ETAG_PATH")
    say "New ODF_ETAG => $new_etag ($etag_type)"
}

main
