# Data format tradeoffs

When picking the data shape for a Drive-backed viewer, three real options:

## Option 1: `.js` file exporting globals (recommended for migrations)

Existing static HTML tools often have a `data.js` file that defines globals like `const ROLES = [...]`. Keep that shape.

**Pros:**
- Zero schema change when migrating
- Inline-into-HTML-template pattern works directly (the JS content gets injected into a `<script>` block)
- Editable in any text editor; readable as plain JS

**Cons:**
- Not human-friendly for non-engineers to edit directly
- Drive's preview shows it as raw text, not formatted

**Edit experience:** download from Drive, edit in Cursor/VSCode, re-upload. Or edit locally then sync. Awkward but workable.

**Use when:** migrating an existing tool, or when the synthesis content is structured in a way that doesn't map cleanly to a Sheet.

## Option 2: `.json` file

Structurally similar to `.js` but pure JSON (no `const X = ...` wrapper).

**Pros:**
- Standard format, parseable by any tool
- Apps Script parses with `JSON.parse(file.getBlob().getDataAsString())`
- Validatable against a schema if needed

**Cons:**
- Same edit-experience problem as `.js` for non-engineers
- No comments (JSON doesn't support them)
- Strict syntax — a missing comma breaks the whole file

**Use when:** building from scratch and you want a clean data contract. Otherwise the cost-of-migration from `.js` to `.json` isn't worth it.

## Option 3: Google Sheet

Multi-tab workbook where each tab is a logical table (Roles, Candidates, Fits, Outreach, Observations).

**Pros:**
- Brianna / Aimee / non-engineers can edit directly
- Native filtering, sorting, conditional formatting
- Sheets revision history per cell (audit trail for free)
- Live collaboration (multiple editors at once)
- Comments on cells for context that doesn't fit in the data itself

**Cons:**
- Nested structures (candidate × fits-per-role) require flattening across multiple sheets, joined by ID
- Adding a new candidate = several rows in several sheets
- Schema changes are harder (need to update both Sheet structure and reader code)
- Apps Script reads are slower than file reads for large datasets

**Use when:** the data is intrinsically tabular AND multiple non-engineers need to edit live. Don't use when the data has rich nested structure (the flatten cost is high).

## Decision matrix

| Need | Recommendation |
|---|---|
| Migrating existing tool with `data.js` | Option 1 |
| Building new, single editor | Option 1 or 2 |
| Multiple editors needing live collab | Option 3 |
| Data has heavy nesting | Option 1 or 2 |
| Data is intrinsically tabular | Option 3 |
| Non-engineers will edit | Option 3 (or build a separate edit UI on top of Option 1) |

## Hybrid (if you really need it)

The "edit in Sheet, render from generated JS" pattern: maintain a Google Sheet as the editable source, run a script that exports the Sheet to a `.js` file in Drive, the viewer reads from the `.js` file. Gets you collaborative editing without paying the flatten cost in the viewer code. More moving parts but worth knowing the option exists.

## Recommendation for the matrix viewer (first concrete use)

Use **Option 1** (existing `matrix-data.js` shape, lives in Drive). Zero migration cost, matches the existing tool. Revisit if/when Brianna actively wants to edit the data live; at that point evaluate Option 3 or hybrid.
