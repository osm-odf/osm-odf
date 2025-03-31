# OSM PBF to CSV Converter

This project provides tools for converting OpenStreetMap (OSM) data to CSV format. It includes two main components:

1. **OSM PBF to CSV Converter** - Converts OSM PBF files to CSV format
2. **OSM Minutely Consumer** - Fetches and processes OSM minutely updates from the Overpass API

## Shared Understanding

Both the Python and Kotlin implementations share a common understanding of the OSM data model and conversion process:

- **Data Types**: Both handle nodes, ways, relations, and tags
- **Output Format**: Both produce CSV files with consistent column structures
- **WKT Geometry**: Both convert OSM geometries to Well-Known Text (WKT) format
- **Environment Variables**: Both use the same environment variables for configuration

## OSM PBF to CSV Converter

The `OsmToCsvConverter` class processes OSM PBF files and outputs four CSV files:

- `*-nodes.csv` - Node data with coordinates
- `*-ways.csv` - Way data with WKT geometry
- `*-relations.csv` - Relation data with member references
- `*-tags.csv` - Tag data for all elements

### Usage

```bash
./gradlew run --args="path/to/file.osm.pbf output/path/for/max/changeset/id"
```

## OSM Minutely Consumer

The `OsmMinutelyConsumer` class fetches and processes OSM minutely updates from the Overpass API. It outputs four CSV files:

- `nodes_<timestamp>.csv` - Node data with coordinates
- `ways_<timestamp>.csv` - Way data with WKT geometry
- `relations_<timestamp>.csv` - Relation data with member references
- `tags_<timestamp>.csv` - Tag data for all elements

### Usage

```bash
# Run the consumer
./gradlew runConsumer

# Build a standalone JAR
./gradlew consumerJar

# Run the JAR
java -jar build/libs/osm-minutely-consumer.jar
```

### Environment Variables

Both implementations use the following environment variables:

- `VERBOSE`: Set to `1` to enable verbose output
- `NODES`: Set to `1` to output node data
- `WAYS`: Set to `1` to output way data
- `RELATIONS`: Set to `1` to output relation data
- `TAGS`: Set to `1` to output tag data
- `ODF_ETAG`: The latest changeset ID processed
- `ODF_NEW_ETAG_PATH`: Path to write the new max changeset ID

## Differences Between Python and Kotlin Implementations

- **XML Parsing**: Python uses ElementTree while Kotlin uses DOM for XML parsing
- **HTTP Client**: Python uses the requests library while Kotlin uses HttpClient from java.net.http
- **Error Handling**: Both implementations handle errors similarly but with language-specific patterns

## Building and Running

```bash
# Build the project
./gradlew build

# Run the OSM PBF to CSV converter
./gradlew run --args="path/to/file.osm.pbf output/path/for/max/changeset/id"

# Run the OSM Minutely Consumer
./gradlew runConsumer
```
