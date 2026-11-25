---
name: er-diagram
description: Draw an interactive entity-relationship (ER) diagram of a database or domain model as one self-contained HTML page or Artifact, in a fixed house style - tables grouped into annotated module boxes, colored headers by table kind, key/index/derived field icons, right-angled lines routed from each foreign-key field to the key it references with crow's-foot ends, zoom and pan, jump-to-module, find-table, and hover cards with full field descriptions, translated table names and summaries. Use this skill whenever the user wants an ER diagram, schema diagram, database diagram, data model picture, entity map or table-relationship overview, or asks to visualize models, entities, migrations or DDL (EF Core, Django, Prisma, TypeORM, Rails, SQL), even when they don't say "ER diagram" - e.g. "draw our tables", "show how the entities connect", "diagram the data model for the new module", "map the database for the onboarding doc".
---

# ER diagrams in the house style

You produce a single HTML page (or an Artifact) that shows a whole schema at once: tables sit in
module boxes on a grid, every relationship is a right-angled line that leaves the exact foreign-key
row and lands on the exact key row, and hovering anything explains it. The engine, styles and page
template are finished and tested; your job is to describe the schema as data, choose a sensible
layout, build, check, and deliver.

```
er-diagram/
├── assets/er-diagram.js      engine: layout, A* line routing, zoom/pan, hover cards, check()
├── assets/er-diagram.css     styles and theme tokens (light and dark), all prefixed --erd-
├── assets/template.html      page shell with toolbar, legend and canvas placeholders
├── scripts/build.sh          model + template → finished page (Artifact form or --standalone)
├── scripts/serve.ps1         tiny local web server for previewing (Windows, no dependencies)
├── references/model-format.md   the MODEL data format, field by field
├── references/layout.md         placing modules and tables; reading check() results
├── references/sources.md        pulling fields, keys and descriptions out of ORM code
└── examples/                 shop.model.js (small, every feature) · visitca.model.js (56 tables)
```

Don't hand-write SVG coordinates or rewrite the engine. The look comes from the engine; consistency
across diagrams is the point of the skill. Spend the effort on the model: accurate fields, honest
descriptions, and a layout that keeps related modules next to each other.

## Workflow

### 1. Collect the schema

Work from the source of truth, in this order: the ORM model classes and their configuration, then
migrations or DDL, then what the user tells you. For each table gather fields (name, type), primary
keys, foreign keys and what they point at, unique and other indexes, nullability of each foreign
key, and any description text the code already carries (`[Description]`, `help_text`, `///` doc
comments, `COMMENT ON COLUMN`). `references/sources.md` has extraction snippets per framework.

When the user is planning changes (new tables, phases, a roadmap), also note which tables and fields
exist today and which arrive later; the format has statuses and phase tags for that.

### 2. Write the model file

Create `<name>.model.js` that defines `var MODEL = { … }`. Read `references/model-format.md` before
writing your first one, and copy the shape of `examples/shop.model.js`. The parts that need judgment:

- **kind** colors the table header: `core` (main business objects), `dep` (owned details that only
  exist under a parent), `link` (many-to-many join tables), `ref` (lookup and reference data), `log`
  (ledgers, events, queues, history). Pick by what the table is for, not by its size.
- **descriptions** say what a field means and how it is used ("Deposit the traveller pays the
  organizer, USD"), not its type. When the code has description text, put it verbatim in the sixth
  slot so the hover card can quote it, and write your own fuller sentence in the fifth. Trivial
  fields (`id`, `created_at`, `slug`…) get sensible text automatically when you leave it empty.
- **alt** is an alternate name in the team's other working language (Russian for the VisitCA team);
  set `altLang` to its BCP 47 code. **summary** is one or two plain sentences on what the table is for.
- **relations** run child → parent: `[childTable, fkField, parentTable, keyField, parentSide,
  childSide, identifying, label]`. Parent side is `"1"` for a required foreign key and `"01"` for a
  nullable one. A relationship is identifying when the foreign key is part of the child's primary key
  (link tables, composite keys).

Every table must appear in exactly one group; the engine refuses to draw otherwise and says which.

### 3. Lay out modules and tables

Groups are modules or bounded contexts, placed on a grid with `at: [column, row]`; inside a group,
`cols` lists columns of tables left to right. The engine computes every coordinate and routes every
line, so layout is only about adjacency:

- put the most-referenced module (usually users/accounts) in the middle, and modules that reference
  each other heavily next to each other;
- inside a group, put a parent table in the column next to its children, and stack small related
  tables in one column;
- give a group a wider `gap` when many lines must pass between its columns (hub tables).

`references/layout.md` has the full method, including a quick way to score grid placements.

### 4. Build

```sh
sh scripts/build.sh model.js out.html --title "Shop data model" --intro "One paragraph for readers." [--standalone]
```

Without `--standalone` the output is in Artifact form (it starts with `<title>`; the Artifact host adds
the document skeleton). Use `--standalone` for a file people open from disk or commit to a repo.

### 5. Preview and check

The in-app browser won't run scripts in a `file://` page, so serve the folder first:

```sh
powershell -File scripts/serve.ps1 -Root <folder with out.html>      # Windows; runs ~30 minutes
python3 -m http.server 8765 --directory <folder>                      # elsewhere
```

Open `http://localhost:8765/out.html`, then run in the page (browser `javascript_tool`):

```js
await ERDiagram.instances[0].check()
```

`failedRoutes`, `throughTables`, `throughHeaders`, `diagonal` and `overlaps` should all be 0.
`overlapHotspots` names the group where lines pile up; widen that group's `gap` (or the layout's
`groupGap` when the hotspot is "between groups") and rebuild. Then take one screenshot zoomed to a
busy module (click its button in the module row) to confirm it reads well. Fonts load from Google
Fonts; without network the page falls back to system fonts and still works.

### 6. Deliver

- **Artifact**: publish the non-standalone build with the Artifact tool (load the artifact-design
  guidance first if you haven't this session; the template already follows its page contract).
- **File**: build with `--standalone` and save where the user asked, e.g. `docs/data-model.html`.
- **Inside an existing page**: copy the CSS into the page's `<style>`, the `<section data-erd="root">`
  markup from the template, the engine in a `<script>`, then `ERDiagram.render(section, MODEL)`.
  Several diagrams can share a page: give each its own root section (the `id`/`for` pair on the
  "Find table" select must then be unique per section).

Tell the user how to read it in a sentence or two (drag, pinch or Ctrl+scroll to zoom, hover for
details) and mention anything you inferred rather than read from code.

## When things go wrong

| Symptom | Cause and fix |
|---|---|
| "Diagram failed to draw: Unknown table X" | A group lists a table name that isn't in `entities` (check spelling and case). |
| "Tables not placed in any group" | Add each listed table to some group's `cols`. |
| "Bad relationship …" | The child or parent table, or one of the two field names, doesn't match the model exactly. |
| `failedRoutes` not empty | The router gave up and drew a fallback path that may cross tables. Increase `groupGap` or move the two modules closer. |
| Lines overlap in one module | Widen that group's `gap`; a hub table (referenced by many) needs room for one lane per line. |
| Diagram is very wide | Split a wide group into more rows of tables (taller columns) or move a group to another grid row. |
| Routing takes several seconds | The canvas is huge; tighten `groupGap` or the column gaps. Routing about 100 lines over 4,400 × 2,300 px takes under a second. |
