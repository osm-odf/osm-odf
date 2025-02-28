
# OpenStreetMap (OSM) Data Processing Tools

## 1. Convert OSM PBF to CSV

Convert OSM PBF files to CSV format for [kamu-osm-demo](https://github.com/jonathanlocke/kamu-osm-demo):

```bash
OsmToCsvConverter new-mexico-latest.osm.pbf
```

## 2. Process OSM Minutely Diffs

The Python consumer script processes OSM minutely diff files and extracts create actions into CSV files.

### Usage

```bash
python3 osm-minutely-changes/consumer.py <url> <nodes.csv> <ways.csv> <relations.csv> <tags.csv>
```

### Example

```bash
python3 osm-minutely-changes/consumer.py \
    https://planet.openstreetmap.org/replication/minute/000/001/000.adiff \
    nodes.csv \
    ways.csv \
    relations.csv \
    tags.csv
```

### Output Files

- `nodes.csv`: Contains created nodes with coordinates
- `ways.csv`: Contains created ways with WKT geometries
- `relations.csv`: Contains created relations with member references
- `tags.csv`: Contains all tags from created elements

Each CSV file includes metadata like timestamp, version, changeset, and user information.
