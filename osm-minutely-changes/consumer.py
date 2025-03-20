#!/usr/bin/env python3
import requests
import xml.etree.ElementTree as ET
import time
import csv
import sys
import io
import os
from datetime import datetime

# epoch in seconds 
current_epoch = int(time.time())

nodes_csv = f"nodes_{current_epoch}"
ways_csv = f"ways_{current_epoch}"
relations_csv = f"relations_{current_epoch}"
tags_csv = f"tags_{current_epoch}"

VERBOSE = os.getenv('VERBOSE', '0') == '1'
NODES = os.getenv('NODES', '0') == '1'
WAYS = os.getenv('WAYS', '0') == '1'
RELATIONS = os.getenv('RELATIONS', '0') == '1'
TAGS = os.getenv('TAGS', '0') == '1'

def fetch_state() -> int:
    """
    Fetch the current adiff state from OSM https://overpass-api.de/api/augmented_diff_status
    """
    response = requests.get("https://overpass-api.de/api/augmented_diff_status")
    return response.text.strip()


def fetch_xml(url):
    """Fetch XML data from a URL and return its content as bytes."""
    response = requests.get(url)
    if response.status_code == 429:
        print(f"Error: Too many requests to {url} (status code 429)")
        sys.exit(1)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch {url} (status code {response.status_code})")
    return response.content


def parse_osm_create(xml_data):
    """
    Parse only the create actions from the OSM XML diff.
    Separates node, way, relation records and extracts tag rows.
    For ways, builds a WKT geometry from <nd> children.
    Returns four lists: nodes_rows, ways_rows, relations_rows, tags_rows.
    """
    tree = ET.parse(io.BytesIO(xml_data))
    root = tree.getroot()

    nodes_rows = []
    ways_rows = []
    relations_rows = []
    tags_rows = []

    # Process each <action> element
    for action in root.findall("action"):
        act_type = action.attrib.get("type")
        if act_type != "create":
            continue  # Only process create actions

        # Find the created element (usually under <new>)
        elem = action.find("new/*")
        if elem is None:
            elem = action.find("*")
        if elem is None:
            continue

        # Convert timestamp to epoch milliseconds
        timestamp = elem.attrib.get("timestamp")
        epochMillis = None
        if timestamp:
            try:
                epochMillis = int(
                    datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").timestamp()
                    * 1000
                )
            except Exception:
                epochMillis = None

        elem_type = elem.tag
        elem_id = elem.attrib.get("id")

        # Extract tags for this element (if any)
        for tag in elem.findall("tag"):
            key = tag.attrib.get("k")
            value = tag.attrib.get("v")
            tags_rows.append(
                {
                    "epochMillis": epochMillis,
                    "type": elem_type,
                    "id": elem_id,
                    "key": key,
                    "value": value,
                }
            )

        if elem_type == "node":
            row = {
                "epochMillis": epochMillis,
                "id": elem_id,
                "version": elem.attrib.get("version"),
                "changeset": elem.attrib.get("changeset"),
                "username": elem.attrib.get("user"),
                "uid": elem.attrib.get("uid"),
                "lat": elem.attrib.get("lat"),
                "lon": elem.attrib.get("lon"),
            }
            nodes_rows.append(row)
        elif elem_type == "way":
            # Build WKT geometry from <nd> children. We expect each <nd> to include lat/lon.
            coords = []
            for nd in elem.findall("nd"):
                # Some OSM diff files might include lat/lon attributes on the nd element;
                # if not, you might need to look up the referenced node.
                lat = nd.attrib.get("lat")
                lon = nd.attrib.get("lon")
                if lat is not None and lon is not None:
                    try:
                        coords.append(
                            (float(lon), float(lat))
                        )  # WKT expects x (lon) then y (lat)
                    except ValueError:
                        continue
            if coords:
                # If the way is closed (>=4 points and first equals last), output as POLYGON.
                if len(coords) >= 4 and coords[0] == coords[-1]:
                    coord_str = ", ".join(f"{pt[0]} {pt[1]}" for pt in coords)
                    wkt_geom = f"POLYGON(({coord_str}))"
                else:
                    coord_str = ", ".join(f"{pt[0]} {pt[1]}" for pt in coords)
                    wkt_geom = f"LINESTRING({coord_str})"
            else:
                wkt_geom = ""
            row = {
                "epochMillis": epochMillis,
                "id": elem_id,
                "version": elem.attrib.get("version"),
                "changeset": elem.attrib.get("changeset"),
                "username": elem.attrib.get("user"),
                "uid": elem.attrib.get("uid"),
                "geometry": wkt_geom,
            }
            ways_rows.append(row)
        elif elem_type == "relation":
            # For relations, as a simple approach we output a comma-separated list of member refs as geometry.
            members = elem.findall("member")
            geometry = ",".join(
                m.attrib.get("ref") for m in members if m.attrib.get("ref")
            )
            row = {
                "epochMillis": epochMillis,
                "id": elem_id,
                "version": elem.attrib.get("version"),
                "changeset": elem.attrib.get("changeset"),
                "username": elem.attrib.get("user"),
                "uid": elem.attrib.get("uid"),
                "geometry": geometry,
            }
            relations_rows.append(row)

    return nodes_rows, ways_rows, relations_rows, tags_rows


def write_csv_dict(rows, csv_file, fieldnames):
    """Write rows (a list of dictionaries) to stdout in CSV format with a given header."""
    # Create a StringIO object to write CSV data
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    
    # Print to stdout with a header indicating which type of data this is
    if VERBOSE:
        print(f"\n--- {csv_file} ---")
        print(output.getvalue())
    output.close()


def main():
    if len(sys.argv) != 1:
        print("Usage: consumer.py")
        sys.exit(1)

    if VERBOSE:
        print("Fetching state...")
    state = fetch_state()
    # that gives me the state number
    # http://overpass-api.de/api/augmented_diff?id=
    url = f"https://overpass-api.de/api/augmented_diff?id={state}"
    if VERBOSE:
        print(f"Fetching {url}")

    try:
        xml_data = fetch_xml(url)
        nodes_rows, ways_rows, relations_rows, tags_rows = parse_osm_create(xml_data)

        # Write nodes CSV with the specified columns.
        if VERBOSE:
            print("\n--- nodes.csv ---")
        if NODES:
            node_fields = [
                    "epochMillis",
                    "id",
                    "version",
                    "changeset",
                    "username",
                    "uid",
                    "lat",
                    "lon",
                ]
            write_csv_dict(nodes_rows, nodes_csv, node_fields)

        # Write ways CSV with the specified columns.
        if WAYS:
            way_fields = [
                "epochMillis",
                "id",
                "version",
                "changeset",
                "username",
                "uid",
                "geometry",
            ]
            write_csv_dict(ways_rows, ways_csv, way_fields)

        # Write relations CSV with the specified columns.
        if RELATIONS:
            relation_fields = [
                "epochMillis",
                "id",
                "version",
                "changeset",
            "username",
            "uid",
                "geometry",
            ]
            write_csv_dict(relations_rows, relations_csv, relation_fields)

        # Write tags CSV with the specified columns.
        if TAGS:
            tags_fields = ["epochMillis", "type", "id", "key", "value"]
            write_csv_dict(tags_rows, tags_csv, tags_fields)

        if VERBOSE:
            print("CSVs written to:")
            print(f"  Nodes: {nodes_csv}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
        
if __name__ == "__main__":
    main()
