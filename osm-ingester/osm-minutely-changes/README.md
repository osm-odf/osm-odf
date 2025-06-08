# OSM Minutely Changes Docker Setup

This directory contains a Dockerized version of the OSM Minutely Changes script that fetches and processes OpenStreetMap minutely updates. The application outputs CSV data to stdout. You can control which types of data are output by setting environment variables.

## Docker Setup

### Prerequisites

- Docker
- Docker Compose

### Environment Variables

The following environment variables can be set to control which types of data are output:

- `VERBOSE`: Set to `1` to enable verbose output
- `NODES`: Set to `1` to output node data
- `WAYS`: Set to `1` to output way data
- `RELATIONS`: Set to `1` to output relation data
- `TAGS`: Set to `1` to output tag data

By default, all data types are disabled, so you will need to set the appropriate environment variables to enable the data you want.

### Building and Running

To build and run the container:

```bash
NODES=1 docker-compose up -d --build
```

This will:
1. Build the Docker image
2. Start the container in detached mode and enable node data output

To run the container and see the output directly:

```bash
docker-compose up
```

### Viewing Logs

Since the application outputs to stdout, you can view the output with:

```bash
docker-compose logs -f
```

This will show the CSV data for nodes, ways, relations, and tags that the application processes.

### Stopping the Container

To stop the container:

```bash
docker-compose down
```

## Redirecting Output

If you want to save the output to a file, you can run:

```bash
docker-compose up > output.csv 2>&1
```

Or to append to an existing file:

```bash
docker-compose up >> output.csv 2>&1
```
