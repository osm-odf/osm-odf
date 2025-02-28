
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
python3 osm-minutely-changes/consumer.py
```

The script will:
1. Fetch the latest state from OSM's augmented diff API
2. Download the corresponding diff file
3. Process only the create actions
4. Write output files to the `data/` directory

### Output Files

Output files are written to the `data/` directory with fixed names:
- `data/nodes.csv`: Contains created nodes with coordinates
- `data/ways.csv`: Contains created ways with WKT geometries  
- `data/relations.csv`: Contains created relations with member references
- `data/tags.csv`: Contains all tags from created elements

Each CSV file includes metadata like timestamp, version, changeset, and user information.
