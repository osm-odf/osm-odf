#!/usr/bin/env python3
import time
import csv
import sys
import os
import osmdiff

# epoch in seconds
current_epoch = int(time.time())

VERBOSE = os.getenv("VERBOSE", 0)
NODES = os.getenv("NODES", 0)
WAYS = os.getenv("WAYS", 0)
RELATIONS = os.getenv("RELATIONS", 0)
MEMBERS = os.getenv("MEMBERS", 0)
TAGS = os.getenv("TAGS", 0)
MINLON = float(os.getenv("MINLON", 0.0))
MINLAT = float(os.getenv("MINLAT", 0.0))
MAXLON = float(os.getenv("MAXLON", 0.0))
MAXLAT = float(os.getenv("MAXLAT", 0.0))

max_changeset_id = 0


def write_csv_stdout(rows, fieldnames):
    """Write rows (a list of dictionaries) as CSV to stdout, filtering only allowed fields."""
    writer = csv.DictWriter(
        sys.stdout, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL
    )
    writer.writeheader()
    if rows and VERBOSE:
        print("DEBUG: first row keys:", list(rows[0].keys()), file=sys.stderr)
    for row in rows:
        # Remove all keys not in fieldnames
        filtered_row = {k: row.get(k, "") for k in fieldnames}
        # Remove extra keys if any exist
        for k in list(row.keys()):
            if k not in fieldnames:
                del row[k]
        writer.writerow(filtered_row)


def to_epoch_millis(ts):
    from datetime import datetime, timezone

    if ts is None:
        return None
    if isinstance(ts, (int, float)):
        # Assume already ms
        return int(ts)
    # Try ISO8601 parsing (e.g. '2025-03-03T11:55:24Z')
    try:
        dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
        return int(dt.replace(tzinfo=timezone.utc).timestamp() * 1000)
    except Exception:
        pass
    # Try as float seconds
    try:
        return int(float(ts) * 1000)
    except Exception:
        return None


def main():
    global max_changeset_id

    if len(sys.argv) != 3:
        print("Usage: consumer.py <sequence_number> <etag_output_path>")
        sys.exit(1)

    sequence_number = int(sys.argv[1])
    etag_output_path = sys.argv[2]

    adiff = None

    print(f"MINLON: {MINLON}, MAXLON: {MAXLON}, MINLAT: {MINLAT}, MAXLAT: {MAXLAT}")

    if MINLON == 0 and MINLAT == 0 and MAXLON == 0 and MAXLAT == 0:
        adiff = osmdiff.AugmentedDiff()
    elif MAXLON <= MINLON or MAXLAT <= MINLAT:
        raise ValueError("max lon / MAXLAT needs to be greater than MINLON / MINLAT")
    elif MINLON < -90 or MINLAT < -180 or MAXLON > 90 or MAXLAT > 180:
        raise ValueError("bounds need to be within valid coordinate range")
    else:
        print(f"instantiating adiff with bbox {MINLON}, {MINLAT}, {MAXLON}, {MAXLAT}")
        adiff = osmdiff.AugmentedDiff(
            minlon=MINLON, minlat=MINLAT, maxlon=MAXLON, maxlat=MAXLAT
        )
    adiff.sequence_number = sequence_number
    adiff.retrieve()

    # hello
    try:
        nodes_rows, ways_rows, relations_rows, members_rows, tags_rows = (
            process_diff_data(adiff)
        )

        output_csv_data(nodes_rows, ways_rows, relations_rows, members_rows, tags_rows)

        log_processing_results(
            nodes_rows, ways_rows, relations_rows, members_rows, tags_rows
        )
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    if VERBOSE:
        print(f"max changeset id: {max_changeset_id}")
        print(f"sequence number: {sequence_number}")
        print(f"etag output path: {etag_output_path}")
    with open(etag_output_path, "w") as fh:
        fh.write(str(sequence_number + 1))


def process_diff_data(adiff):
    """Process OSM diff data and extract rows for each entity type."""
    global max_changeset_id

    nodes_rows = []
    ways_rows = []
    relations_rows = []
    members_rows = []
    tags_rows = []

    for o in adiff.create:
        # Update max changeset ID
        max_changeset_id = max(max_changeset_id, int(o.attribs.get("changeset", 0)))

        # Process by entity type
        if isinstance(o, osmdiff.Node):
            process_node(o, nodes_rows)
        elif isinstance(o, osmdiff.Way):
            process_way(o, ways_rows)
        elif isinstance(o, osmdiff.Relation):
            process_relation(o, relations_rows, members_rows)

        # Process tags for all entity types
        process_tags(o, tags_rows)

    return nodes_rows, ways_rows, relations_rows, members_rows, tags_rows


def process_node(node, nodes_rows):
    """Process a single node and add it to nodes_rows."""
    row = {
        "epochMillis": to_epoch_millis(node.attribs.get("timestamp")),
        "id": node.attribs.get("id"),
        "version": node.attribs.get("version"),
        "changeset": node.attribs.get("changeset"),
        "username": node.attribs.get("user"),
        "uid": node.attribs.get("uid"),
        "lat": node.attribs.get("lat"),
        "lon": node.attribs.get("lon"),
    }
    nodes_rows.append(row)


def process_way(way, ways_rows):
    """Process a single way and add it to ways_rows."""
    row = {
        "epochMillis": to_epoch_millis(way.attribs.get("timestamp")),
        "id": way.attribs.get("id"),
        "version": way.attribs.get("version"),
        "changeset": way.attribs.get("changeset"),
        "username": way.attribs.get("user"),
        "uid": way.attribs.get("uid"),
        "geometry": way.attribs.get("geometry"),
    }
    ways_rows.append(row)


def process_relation(relation, relations_rows, members_rows):
    """Process a single relation and add it to relations_rows and its members to members_rows."""
    row = {
        "epochMillis": to_epoch_millis(relation.attribs.get("timestamp")),
        "id": relation.attribs.get("id"),
        "version": relation.attribs.get("version"),
        "changeset": relation.attribs.get("changeset"),
        "username": relation.attribs.get("user"),
        "uid": relation.attribs.get("uid"),
        "geometry": relation.attribs.get("geometry"),
    }
    relations_rows.append(row)

    # Process relation members
    for m in getattr(relation, "members", []):
        members_rows.append(
            {
                "relationId": relation.attribs.get("id"),
                "memberId": m.attribs.get("ref"),
                "memberRole": m.attribs.get("role"),
                "memberType": m.attribs.get("type"),
            }
        )


def process_tags(entity, tags_rows):
    """Process tags for an entity and add them to tags_rows."""
    for k, v in entity.attribs.items():
        if k == "id":
            continue

        osm_type = "node"
        if isinstance(entity, osmdiff.Way):
            osm_type = "way"
        elif isinstance(entity, osmdiff.Relation):
            osm_type = "relation"

        tags_rows.append(
            {
                "epochMillis": to_epoch_millis(entity.attribs.get("timestamp")),
                "type": osm_type,
                "id": entity.attribs.get("id"),
                "key": k,
                "value": v,
            }
        )


def output_csv_data(nodes_rows, ways_rows, relations_rows, members_rows, tags_rows):
    """Output CSV data for all OSM entity types."""
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
        write_csv_stdout(nodes_rows, node_fields)

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
        write_csv_stdout(ways_rows, way_fields)

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
        write_csv_stdout(relations_rows, relation_fields)

    if MEMBERS:
        members_fields = ["relationId", "memberId", "memberRole", "memberType"]
        write_csv_stdout(members_rows, members_fields)

    if TAGS:
        tags_fields = ["epochMillis", "type", "id", "key", "value"]
        write_csv_stdout(tags_rows, tags_fields)


def log_processing_results(
    nodes_rows, ways_rows, relations_rows, members_rows, tags_rows
):
    """Log processing results if in verbose mode."""
    if not VERBOSE:
        return

    print("Processing complete")
    if NODES:
        print(f"Processed {len(nodes_rows)} nodes")
    if WAYS:
        print(f"Processed {len(ways_rows)} ways")
    if RELATIONS:
        print(f"Processed {len(relations_rows)} relations")
    if MEMBERS:
        print(f"Processed {len(members_rows)} members")
    if TAGS:
        print(f"Processed {len(tags_rows)} tags")


if __name__ == "__main__":
    main()
