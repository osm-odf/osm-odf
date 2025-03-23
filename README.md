
# OpenStreetMap (OSM) Data Processing Tools

## 1. Convert OSM PBF to CSV

Convert OSM PBF files to CSV format for [kamu-osm-demo](https://github.com/jonathanlocke/kamu-osm-demo):

### Using Docker

1. Build the image:
```bash
docker build -t osm-pbf-to-csv -f osm-pbf-to-csv/Dockerfile .
```

2. Run the converter with a PBF file:
```bash
docker run -v /path/to/your/file.osm.pbf:/input/input.osm.pbf -v /path/to/output:/output osm-pbf-to-csv
```

3. Output files will be written to the mounted output directory with names:
- `input-nodes.csv`
- `input-ways.csv` 
- `input-relations.csv`
- `input-tags.csv`
- `input-bounds.txt`

### Running Directly

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
