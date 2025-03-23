#!/bin/sh
docker run \
-v \
../data/berlin/berlin-latest-internal.osm.pbf:/input/input.osm.pbf \
osm-odf-osm-pbf-to-csv:latest