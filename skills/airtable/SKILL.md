---
name: airtable
description: Interact with Airtable bases via the REST API. Use when the user wants to list, search, create, or update Airtable records, manage attachments, or query tables.
---

# Airtable

Read, create, update, and search records in Airtable bases. Handles attachment fields (upload via URL, download for processing).

## Configuration

Requires environment variables:
- `AIRTABLE_API_KEY` — personal access token (pat...) or API key
- `AIRTABLE_BASE_ID` — base ID (appXXXXXXXXXXXXXX)

## Usage

Run `./run.sh` from this skill's directory with a subcommand:

```bash
# List available tables
./run.sh tables

# List records (with optional filter)
./run.sh list "Tasks" --filter "{Status}='In Progress'"

# Search records by field value
./run.sh search "Tasks" "Name" "Deploy API"

# Get a single record
./run.sh get "Tasks" recXXXXXXXXXXXXXX

# Create a record
./run.sh create "Tasks" '{"Name": "New task", "Status": "Todo"}'

# Update a record
./run.sh update "Tasks" recXXXXXXXXXXXXXX '{"Status": "Done"}'

# Add attachment (by URL)
./run.sh attach "Tasks" recXXXXXXXXXXXXXX "Attachments" "https://example.com/file.pdf"

# Download attachment to output/
./run.sh download "Tasks" recXXXXXXXXXXXXXX "Attachments"
```

## Options

- `--filter FORMULA` — Airtable filter formula (e.g., `{Status}='Active'`)
- `--fields FIELD1,FIELD2` — comma-separated list of fields to return
- `--max N` — max number of records (default: 100)
- `--sort FIELD` — sort by field name
- `--desc` — sort descending (default ascending)
- `--view NAME` — use a specific Airtable view

## Instructions for Claude

1. If the user mentions Airtable, tables, or records — use this skill
2. Run `./run.sh tables` first to discover available tables if the user hasn't specified one
3. Use `--filter` with Airtable formula syntax for complex queries
4. For attachments: Airtable requires a publicly accessible URL. If the user has a local file, note that it must be hosted somewhere first (e.g., uploaded to a file hosting service)
5. Downloaded attachments are saved to `output/` — read them from there
6. Results are printed as JSON. Parse them to present data clearly to the user
7. When creating/updating records, field names are case-sensitive and must match exactly
