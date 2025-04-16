#!/usr/bin/env python3
import requests
import time
import csv
import sys
import io
import os
from datetime import datetime
import osmdiff

# epoch in seconds
current_epoch = int(time.time())

VERBOSE = os.getenv("VERBOSE", 0)
NODES = os.getenv("NODES", 0)
WAYS = os.getenv("WAYS", 0)
RELATIONS = os.getenv("RELATIONS", 0)
MEMBERS = os.getenv("MEMBERS", 0)
TAGS = os.getenv("TAGS", 0)


max_changeset_id = 0


def write_csv_stdout(rows, fieldnames):
    """Write rows (a list of dictionaries) as CSV to stdout, filtering only allowed fields."""
    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
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


def main():
    max_changeset_id = 0
    if len(sys.argv) != 3:
        print("Usage: consumer.py <sequence_number> <etag_output_path>")
        sys.exit(1)

    sequence_number = sys.argv[1]
    etag_output_path = sys.argv[2]

    adiff = osmdiff.AugmentedDiff()
    adiff.sequence_number = sequence_number
    adiff.retrieve()

    try:
        # Transform osmdiff objects to expected CSV dicts
        from datetime import datetime, timezone
        def to_epoch_millis(ts):
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

        nodes_rows = []
        for o in adiff.create:
            max_changeset_id = max(max_changeset_id, int(o.attribs.get("changeset", 0)))
            if isinstance(o, osmdiff.Node):
                row = {
                    "epochMillis": to_epoch_millis(o.attribs.get("timestamp")),
                    "id": o.attribs.get("id"),
                    "version": o.attribs.get("version"),
                    "changeset": o.attribs.get("changeset"),
                    "username": o.attribs.get("user"),
                    "uid": o.attribs.get("uid"),
                    "lat": o.attribs.get("lat"),
                    "lon": o.attribs.get("lon"),
                }
                nodes_rows.append(row)

        ways_rows = []
        for o in adiff.create:
            max_changeset_id = max(max_changeset_id, int(o.attribs.get("changeset", 0)))
            if isinstance(o, osmdiff.Way):
                row = {
                    "epochMillis": to_epoch_millis(o.attribs.get("timestamp")),
                    "id": o.attribs.get("id"),
                    "version": o.attribs.get("version"),
                    "changeset": o.attribs.get("changeset"),
                    "username": o.attribs.get("user"),
                    "uid": o.attribs.get("uid"),
                    "geometry": o.attribs.get("geometry"),
                }
                ways_rows.append(row)

        relations_rows = []
        for o in adiff.create:
            if isinstance(o, osmdiff.Relation):
                row = {
                    "epochMillis": to_epoch_millis(o.attribs.get("timestamp")),
                    "id": o.attribs.get("id"),
                    "version": o.attribs.get("version"),
                    "changeset": o.attribs.get("changeset"),
                    "username": o.attribs.get("user"),
                    "uid": o.attribs.get("uid"),
                    "geometry": o.attribs.get("geometry"),
                }
                max_changeset_id = max(max_changeset_id, int(o.attribs.get("changeset", 0)))
                relations_rows.append(row)

        # Members and tags may need similar filtering/flattening if used
        members_rows = []
        for o in adiff.create:
            if isinstance(o, osmdiff.Relation):
                for m in getattr(o, 'members', []):
                    members_rows.append({
                        "relationId": o.attribs.get("id"),
                        "memberId": m.attribs.get("ref"),
                        "memberRole": m.attribs.get("role"),
                        "memberType": m.attribs.get("type"),
                    })
        
        tags_rows = []
        for o in adiff.create:
            # extract all tags
            for k, v in o.attribs.items():
                if k == "id":
                    continue
                osm_type = "node" if isinstance(o, osmdiff.Node) else "way" if isinstance(o, osmdiff.Way) else "relation"
                tags_rows.append({
                    "epochMillis": to_epoch_millis(o.attribs.get("timestamp")),
                    # type is "node", "way", or "relation"
                    "type": osm_type,
                    "id": o.attribs.get("id"),
                    "key": k,
                    "value": v,
                })  

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

        if VERBOSE:
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
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    if VERBOSE:
        print(f"max changeset id: {max_changeset_id}")
    with open(etag_output_path, "w") as fh:
        fh.write(str(max_changeset_id))


if __name__ == "__main__":
    main()
