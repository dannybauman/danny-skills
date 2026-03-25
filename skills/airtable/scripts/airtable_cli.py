#!/usr/bin/env python3
"""CLI for interacting with Airtable bases via the REST API."""

import argparse
import json
import os
import sys
import urllib.parse
from pathlib import Path

import requests

API_URL = "https://api.airtable.com/v0"
META_URL = "https://api.airtable.com/v0/meta/bases"


def get_config():
    api_key = os.environ.get("AIRTABLE_API_KEY")
    base_id = os.environ.get("AIRTABLE_BASE_ID")
    if not api_key:
        print("Error: AIRTABLE_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
    if not base_id:
        print("Error: AIRTABLE_BASE_ID environment variable not set", file=sys.stderr)
        sys.exit(1)
    return api_key, base_id


def headers(api_key):
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def table_url(base_id, table_name):
    return f"{API_URL}/{base_id}/{urllib.parse.quote(table_name, safe='')}"


def cmd_tables(args):
    api_key, base_id = get_config()
    resp = requests.get(
        f"{META_URL}/{base_id}/tables",
        headers=headers(api_key),
    )
    resp.raise_for_status()
    tables = resp.json().get("tables", [])
    result = [{"id": t["id"], "name": t["name"], "fields": [f["name"] for f in t.get("fields", [])]} for t in tables]
    print(json.dumps(result, indent=2))


def cmd_list(args):
    api_key, base_id = get_config()
    params = {}
    if args.filter:
        params["filterByFormula"] = args.filter
    if args.fields:
        for i, f in enumerate(args.fields.split(",")):
            params[f"fields[{i}]"] = f.strip()
    if args.max:
        params["pageSize"] = min(int(args.max), 100)
    if args.sort:
        params["sort[0][field]"] = args.sort
        params["sort[0][direction]"] = "desc" if args.desc else "asc"
    if args.view:
        params["view"] = args.view

    all_records = []
    max_records = int(args.max) if args.max else 100
    offset = None

    while len(all_records) < max_records:
        if offset:
            params["offset"] = offset
        params["pageSize"] = min(100, max_records - len(all_records))

        resp = requests.get(
            table_url(base_id, args.table),
            headers=headers(api_key),
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()
        all_records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break

    print(json.dumps(all_records[:max_records], indent=2))


def cmd_search(args):
    api_key, base_id = get_config()
    # Escape single quotes in value for Airtable formula
    value = args.value.replace("'", "\\'")
    formula = f"{{{args.field}}}='{value}'"

    params = {"filterByFormula": formula}
    if args.max:
        params["pageSize"] = min(int(args.max), 100)

    resp = requests.get(
        table_url(base_id, args.table),
        headers=headers(api_key),
        params=params,
    )
    resp.raise_for_status()
    print(json.dumps(resp.json().get("records", []), indent=2))


def cmd_get(args):
    api_key, base_id = get_config()
    resp = requests.get(
        f"{table_url(base_id, args.table)}/{args.record_id}",
        headers=headers(api_key),
    )
    resp.raise_for_status()
    print(json.dumps(resp.json(), indent=2))


def cmd_create(args):
    api_key, base_id = get_config()
    fields = json.loads(args.fields_json)
    resp = requests.post(
        table_url(base_id, args.table),
        headers=headers(api_key),
        json={"fields": fields},
    )
    resp.raise_for_status()
    print(json.dumps(resp.json(), indent=2))


def cmd_update(args):
    api_key, base_id = get_config()
    fields = json.loads(args.fields_json)
    resp = requests.patch(
        f"{table_url(base_id, args.table)}/{args.record_id}",
        headers=headers(api_key),
        json={"fields": fields},
    )
    resp.raise_for_status()
    print(json.dumps(resp.json(), indent=2))


def cmd_attach(args):
    api_key, base_id = get_config()
    # First get existing attachments
    resp = requests.get(
        f"{table_url(base_id, args.table)}/{args.record_id}",
        headers=headers(api_key),
    )
    resp.raise_for_status()
    existing = resp.json().get("fields", {}).get(args.field, [])

    # Append new attachment
    attachments = list(existing) + [{"url": args.url}]

    resp = requests.patch(
        f"{table_url(base_id, args.table)}/{args.record_id}",
        headers=headers(api_key),
        json={"fields": {args.field: attachments}},
    )
    resp.raise_for_status()
    print(json.dumps(resp.json(), indent=2))


def cmd_download(args):
    api_key, base_id = get_config()
    resp = requests.get(
        f"{table_url(base_id, args.table)}/{args.record_id}",
        headers=headers(api_key),
    )
    resp.raise_for_status()
    record = resp.json()
    attachments = record.get("fields", {}).get(args.field, [])

    if not attachments:
        print(f"No attachments found in field '{args.field}'", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)

    downloaded = []
    for att in attachments:
        url = att.get("url")
        filename = att.get("filename", url.split("/")[-1].split("?")[0])
        out_path = output_dir / filename

        file_resp = requests.get(url)
        file_resp.raise_for_status()
        out_path.write_bytes(file_resp.content)
        downloaded.append({"filename": filename, "path": str(out_path), "size": len(file_resp.content)})

    print(json.dumps(downloaded, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Airtable CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # tables
    subparsers.add_parser("tables", help="List tables in the base")

    # list
    p_list = subparsers.add_parser("list", help="List records from a table")
    p_list.add_argument("table", help="Table name")
    p_list.add_argument("--filter", help="Airtable filter formula")
    p_list.add_argument("--fields", help="Comma-separated field names")
    p_list.add_argument("--max", default="100", help="Max records to return")
    p_list.add_argument("--sort", help="Sort by field")
    p_list.add_argument("--desc", action="store_true", help="Sort descending")
    p_list.add_argument("--view", help="Airtable view name")

    # search
    p_search = subparsers.add_parser("search", help="Search records by field value")
    p_search.add_argument("table", help="Table name")
    p_search.add_argument("field", help="Field name to search")
    p_search.add_argument("value", help="Value to match")
    p_search.add_argument("--max", default="100", help="Max records")

    # get
    p_get = subparsers.add_parser("get", help="Get a single record")
    p_get.add_argument("table", help="Table name")
    p_get.add_argument("record_id", help="Record ID (recXXX)")

    # create
    p_create = subparsers.add_parser("create", help="Create a record")
    p_create.add_argument("table", help="Table name")
    p_create.add_argument("fields_json", help="JSON object of field values")

    # update
    p_update = subparsers.add_parser("update", help="Update a record")
    p_update.add_argument("table", help="Table name")
    p_update.add_argument("record_id", help="Record ID (recXXX)")
    p_update.add_argument("fields_json", help="JSON object of field values to update")

    # attach
    p_attach = subparsers.add_parser("attach", help="Add attachment by URL")
    p_attach.add_argument("table", help="Table name")
    p_attach.add_argument("record_id", help="Record ID (recXXX)")
    p_attach.add_argument("field", help="Attachment field name")
    p_attach.add_argument("url", help="URL of file to attach")

    # download
    p_download = subparsers.add_parser("download", help="Download attachments")
    p_download.add_argument("table", help="Table name")
    p_download.add_argument("record_id", help="Record ID (recXXX)")
    p_download.add_argument("field", help="Attachment field name")

    args = parser.parse_args()

    commands = {
        "tables": cmd_tables,
        "list": cmd_list,
        "search": cmd_search,
        "get": cmd_get,
        "create": cmd_create,
        "update": cmd_update,
        "attach": cmd_attach,
        "download": cmd_download,
    }

    try:
        commands[args.command](args)
    except requests.HTTPError as e:
        error_body = ""
        if e.response is not None:
            try:
                error_body = e.response.json()
            except Exception:
                error_body = e.response.text
        print(json.dumps({"error": str(e), "details": error_body}, indent=2), file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON — {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
