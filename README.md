
# OpenStreetMap (OSM) Data Processing Tools

## 1. Convert OSM PBF to CSV

Convert OSM PBF files to CSV format for [kamu-osm-demo](https://github.com/jonathanlocke/kamu-osm-demo):

### Using Docker

1. Build the image:
```bash
cd osm-ingester
docker build -t osm-ingester  .
```

2. Run the converter with a PBF file:
```bash
docker run -e NODES=1 -e ODF_NEW_ETAG_PATH=/tmp/etag.txt -v /tmp:/tmp osm-ingester:latest
```

When you first run it, there will not be an `etag.txt` file, so it will create one with a timestamp.

The second and subsequent times you run it, it will use the `etag.txt` file to determine which changes to process.

