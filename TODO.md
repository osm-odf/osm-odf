TODO

- Bounding box around Berlin for minutely updates
- S3 bucket
- What would a minimal demo look like?
-


---

Created docker image but should it be separate for nodes / ways / relations or should the CSV just be one file?

Next up:
- Find a way to get an OSM PBF programatically that has all the user data
	- One thing we could do? is to



---

## 2025-03-28

Stuck with docker composition
Needed steps:
1. Check if data exists at all
1a. If not, run initial PBF seed and set initial ETAG vars
1b. If yes, read ETAG and run minutely


```
#!/bin/sh
set -e

# Define data directory and ETAG file location
DATA_DIR="/app/data"
ETAG_FILE="${DATA_DIR}/etag.txt"

# Create data directory if it doesn't exist
mkdir -p ${DATA_DIR}

# Function to run initial PBF seed
run_initial_seed() {
  echo "No existing data found. Running initial PBF seed..."

  # Download and process initial PBF file
  # Replace with your actual PBF processing commands
  /path/to/osm-pbf-to-csv

  # Store initial ETAG
  INITIAL_ETAG=$(date +%s)
  echo "${INITIAL_ETAG}" > ${ETAG_FILE}

  echo "Initial seed completed successfully."
}

# Function to run minutely updates
run_minutely_updates() {
  echo "Existing data found. Running minutely updates..."

  # Read current ETAG
  CURRENT_ETAG=$(cat ${ETAG_FILE})
  echo "Current ETAG: ${CURRENT_ETAG}"

  # Run minutely update process
  # Replace with your actual minutely update commands
  /path/to/osm-minutely-changes

  # Update ETAG after successful update
  NEW_ETAG=$(date +%s)
  echo "${NEW_ETAG}" > ${ETAG_FILE}

  echo "Minutely updates completed successfully."
}

# Main logic - check if data exists
if [ ! -f "${ETAG_FILE}" ] || [ ! -s "${ETAG_FILE}" ]; then
  # No ETAG file or empty file - run initial seed
  run_initial_seed
else
  # ETAG file exists - run minutely updates
  run_minutely_updates
fi

# Optional: Add loop for continuous operation
# while true; do
#   sleep 60
#   run_minutely_updates
# done
```

```
FROM alpine:latest

# Install required dependencies
RUN apk add --no-cache docker curl

# Set up working directory
WORKDIR /app

# Copy the ingester script and other tools
COPY osm-ingester.sh .
COPY your-other-tools/ /app/
RUN chmod +x /app/osm-ingester.sh
RUN chmod +x /app/your-other-tools/*

# Create volume for persistent data
VOLUME /app/data

ENTRYPOINT ["/app/osm-ingester.sh"]
```

END OF SESSION:

➜  osm-ingester git:(docker_wip) ✗ docker run osm-ingester:latest
Checking ODF_ETAG environment variable...
File /tmp/etag.txt does not exist, ODF_ETAG not set
Running osm-pbf-to-csv...
Error: Unable to access jarfile /app/app.jar


== Sequence numbers and changeset IDs

From pbf to csv we get
- latest changeset id
- latest timestamp

Then for OSM minutely

- convert changeset id or timestamp to sequence

`osm replication minute --since "$(date -v -5M -u +"%Y-%m-%dT%H:%M:%SZ")" | head -n 1 | awk '{print $1}'`

`osm replication minute --since "$(date -r 123456789")" | head -n 1 | awk '{print $1}'`

where 12345... is the epoch timestamp

20250406
Need to amend shell script with conversion from timestamp to sequence number:
something like
```
ODF_ETAG = `osm replication minute --since "$(date -r $ODF_ETAG")" | head -n 1 | awk '{print $1}'`
```

Then also look at the Python script where we use the osmdiff library

I am going to split out the python project into a git submodule -- easier to work with in the IDE



20250410

(base) ➜  osm-ingester git:(main) ✗ docker run -e NODES=1 -v /tmp:/tmp osm-ingester:latest
NODES = 1
WAYS =
RELATIONS =
TAGS =
MEMBERS =
ODF_ETAG => -1744302620640
ODF_NEW_ETAG_PATH => /tmp/etag.txt
Downloading minutely augmented diff #timestamp=1744302620640
utc_date=2025-04-10T16:30:20Z
6551207 from Overpass...
Usage: consumer.py

Need to add output path to script
So ETAG needs to be written to that path
and the actual CSV needs to go to STDOUT based on which type is set

ALso need to add berlin bbox to python script

20250416

consecutive runs of the docker container just run the kotlin program over and over.
Need to figure out why etag.txt is not being interpreted / loaded / whatever

20250509

The OsmToCsvConverter app reads berlin-latest-internal.osm.pbf and finds the max
timestamp to be something in recent time like the last few minutes. WHY!??!


20250518

https://wiki.openstreetmap.org/wiki/Overpass_API/Augmented_Diffs#Deriving_augmented_diff_(%22adiff%22)_identifier_from_a_timestamp:
The augmented_diff API call

On overpass-api.de exists an API that allows to filter the Augmented Diffs already on the server. The base URL is

 http://overpass-api.de/api/augmented_diff?

It accepts the following two arguments:

    id= is mandatory and is the id of the Augmented Diff to process
    bbox= is optional and is a min_lon,min_lat,max_lon,max_lat limited bounding box of the area of interest


So next up is:
1. Check what happens when we're all the way caught up
2. Implement rectangle BBOX (see above)

6/6/25

BBOX of extract
13.083,52.332 x 13.782,52.687

docker run -e NODES=1 -e MINLON=13.083 -e MINLAT=52.332 -e MAXLON=13.782 -e MAXLAT=52.687 -v /tmp:/tmp osm-ingester:latest | less

error:
osm-odf/osm-ingester on  main [!] on ☁️  mvexel@gmail.com
❯ docker run -e NODES=1 -e MINLON=13.083 -e MINLAT=52.332 -e MAXLON=13.782 -e MAXLAT=52.687 -v /tmp:/tmp osm-ingester:latest > /dev/null

osm-odf/osm-ingester on  main [!] on ☁️  mvexel@gmail.com took 20s
❯ cat /tmp/etag.txt
-0

20250608

Version number is not interpreted correctly:

```
❯ docker run -e NODES=1 -e MINLON=9.98 -e MINLAT=53.44 -e MAXLON=10.00 -e MAXLAT=53.46 -v /tmp:/tmp osm-ingester:latest
NODES = 1
WAYS =
RELATIONS =
TAGS =
MEMBERS =
ODF_ETAG => 6698250
ODF_NEW_ETAG_PATH => /tmp/etag.txt
Downloading minutely augmented diff #6698250 from Overpass...
MINLON: 9.98, MAXLON: 10.0, MINLAT: 53.44, MAXLAT: 53.46
instantiating adiff with bbox 9.98, 53.44, 10.0, 53.46
epochMillis,id,version,changeset,username,uid,lat,lon
1749327901000,12895640020,1,167326499,Wolfgang Holtz,8292344,53.4522237,9.9962891
Next sequence number was written to /tmp/etag.txt
Done
New ODF_ETAG => 6698251 (sequence number)
```

source:

```
<action type="modify">
<old>
  <node id="33820695" lat="53.4569215" lon="9.9865314" version="19" timestamp="2023-05-19T20:41:52Z" changeset="136316149" uid="15763635" user="sundew_repair">
    <tag k="tactile_paving" v="no"/>
    <tag k="bicycle" v="yes"/>
    <tag k="crossing" v="unmarked"/>
    <tag k="crossing:island" v="yes"/>
    <tag k="highway" v="crossing"/>
  </node>
</old>
<new>
  <node id="33820695" lat="53.4569215" lon="9.9865314" version="20" timestamp="2025-06-07T20:25:01Z" changeset="167326499" uid="8292344" user="Wolfgang Holtz">
    <tag k="bicycle" v="yes"/>
    <tag k="crossing" v="unmarked"/>
    <tag k="crossing:island" v="yes"/>
    <tag k="crossing:markings" v="no"/>
    <tag k="highway" v="crossing"/>
    <tag k="tactile_paving" v="no"/>
  </node>
</new>
</action>
```
