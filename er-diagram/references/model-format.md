# MODEL format

A model file is plain JavaScript that defines one variable, `MODEL`. Keeping it as JS (not JSON) lets
you add comments and build parts in helper variables, as `examples/visitca.model.js` does.

```js
var MODEL = {
  title: "Shop data model",            // used in the SVG's accessible label
  altLang: "ru",                        // BCP 47 code of the alternate table names (optional)
  sourceLabel: "`help_text` on {entity}", // how hover cards cite source text; {entity} = table name, `x` = code style
  kinds: { core: "Core entity" },       // optional: relabel table kinds in the legend and cards
  layout: { colGap: 96, groupGap: 150 }, // optional spacing, see below
  entities: { /* table name → table */ },
  relations: [ /* child → parent links */ ],
  groups: [ /* modules on a grid */ ]
};
```

## entities

```js
Order: {
  kind: "core",            // core | dep | link | ref | log
  status: "changed",       // optional: current | changed | new | future | later
  phase: "P2",             // optional: when a new table arrives ("P2", "V2", "Q3")
  alt: "Заказ",            // optional: alternate-language name, shown big in the hover card
  summary: "A customer's order with its status and total.",   // optional, one or two sentences
  badge: "beta",           // optional: override the header badge text
  fields: [
    // [name, type, flags, phase tag, description, source text]
    ["id", "bigint", "P"],
    ["customer_id", "bigint", "F", "", "Who placed the order.", "Customer"],
    ["promo_code", "varchar", "", "P1", "Promo code applied at checkout."]
  ]
}
```

### kind

| kind | Header color | Use for |
|---|---|---|
| `core` | blue | Main business objects people create and manage (Order, Product, User). |
| `dep` | green | Owned details that only exist under a parent (OrderLine, ProductImage). |
| `link` | amber | Many-to-many join tables, usually with a composite key (Wishlist, ArticleTag). |
| `ref` | violet | Lookup and reference data (Country, Category, Currency, Language). |
| `log` | slate | Ledgers, events, queues, history (Payment, AuditLog, Notification). |

### status and phase

Leave `status` out entirely when you're documenting a schema as it is; the diagram then shows no
badges or status chips. Use statuses when the diagram doubles as a plan:

| status | Header badge | Hover card |
|---|---|---|
| `current` | none | "Exists today" |
| `changed` | CHANGED | "Exists today; changes in P1, P2" (from the field tags) |
| `new` | NEW P2 | "New in P2" |
| `future` | V2 (the phase) | "Planned for V2" |
| `later` | NOT PLANNED | "Not planned yet" |

`"v2"` is accepted as shorthand for `future` with phase V2.

### fields

1. **name**: exactly as in the code or database.
2. **type**: short logical type (`uuid`, `varchar`, `decimal`, `jsonb`, or a value-object name such
   as `LocalizedString[]`). Keep it under about 22 characters; long types widen the whole column.
3. **flags**: any combination of `P` primary key, `F` foreign key, `U` unique, `I` indexed,
   `D` derived (a counter or cache kept in sync by code). The row icon shows the most important
   one: P/F keys, then U, D, I. Composite primary keys mark every part with `P`.
4. **phase tag**: short label shown as a chip on the row (`P1`, `D1`, `V2`) when the field is added
   or changed later. Leave empty for fields that exist and stay as they are.
5. **description**: what the field means, in a sentence. Empty is fine for `id`, `created_at`,
   `updated_at`, `deleted_at`, `slug`, `sort_order`/`position`; the engine fills those in.
6. **source text**: description text that already exists in the code, copied verbatim. The hover
   card quotes it under `sourceLabel`, and its presence also tells the card that the field exists
   today (so a phase tag reads "Changes in P1" rather than "New in P1").

## relations

```js
// [child, child FK field, parent, parent key, parent side, child side, identifying, label]
["OrderLine", "order_id", "Order", "id", "1", "1n", false, "contains"]
```

- **parent side** `"1"`: the foreign key is required (exactly one parent). `"01"`: nullable (zero or one).
- **child side** `"0n"`: a parent can have zero or more children (the usual case). `"1n"`: at least one
  (an order always has a line).
- **identifying** `true` when the foreign key is part of the child's primary key; drawn solid.
  Everything else is drawn dashed.
- **label**: a short verb phrase for the hover card ("contains", "ships to").
- A table may reference itself (a category's parent); the line loops on the table's right side.
- Each foreign-key field should carry `F` in its flags so the row shows the blue key.

## groups

```js
{ id: "orders", short: "Orders", title: "Orders and payments", note: "From checkout to delivery",
  at: [1, 1], gap: 96, cols: [["Order"], ["OrderLine", "Payment", "Shipment"]] }
```

- **at**: `[grid column, grid row]`, zero-based. The grid grows to fit; cells in a column share a width
  and cells in a row share a height, and each group is centered in its cell.
- **cols**: columns of tables, left to right; tables in a column stack top to bottom.
- **short**: label of the module's zoom button. **title** and **note** are drawn in the group's header.
- **gap**: horizontal space between this group's columns (default `layout.colGap`, 96). Raise it for
  groups whose columns carry many lines.

## layout

All optional, in pixels: `colGap` (96, between columns inside a group), `rowGap` (30, between stacked
tables), `groupGap` (150, between groups), `groupPad` (30, inside a group's border), `margin` (60).

## Short keys

The engine also accepts the compact keys used in `examples/visitca.model.js`: `k` = kind,
`s` = status, `p` = phase, `ru` = alt, `sum` = summary, `f` = fields, and `g` = at in groups.
