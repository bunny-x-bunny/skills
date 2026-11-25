# Layout: placing modules and tables

The engine positions every table and routes every line; you choose only which module goes in which
grid cell and how tables are arranged into columns inside each module. Good choices keep lines
short and spread out. Bad ones still draw correctly, just with longer, busier lines.

## Placing modules on the grid

1. Count cross-module relationships. For every pair of groups, count the relationships whose child is
   in one and parent in the other. Write the counts down; a dozen pairs is typical.
2. Put the hub in the middle. The group referenced most (users and accounts, almost always) goes in
   the center cell of a 3 × 3 grid, or a central cell of a 2 × N grid.
3. Score candidate placements. Score = Σ count × (|Δcolumn| + |Δrow|) over all pairs. Try a few
   arrangements by swapping groups and keep the lowest score. For the 9-module VisitCA model the
   difference between a naive and a scored placement was about 15%, and it showed: fewer lines cross
   the whole canvas.
4. Balance the grid. Groups in one grid column share its width, so avoid putting a 5-column group
   above a 1-column one if another arrangement scores nearly as well.

Fewer than 4 groups: a single row or a 2 × 2 grid is fine. One group: just one cell.

## Arranging tables inside a module

- A parent belongs in a column next to its children (left or right). Lines then run straight across
  one gap.
- Stack small tables that hang off the same parent in one column (images, slots, rules).
- Put tables that reference other modules on the side facing those modules: if most lines go to the
  module on the right, put the referencing table in the rightmost column.
- Tall tables (30+ fields) get a column of their own; stacking under them makes the group very tall.
- Two to five columns per group reads well. Six or more makes the grid column very wide.

## Gaps

Each line needs its own 8 px lane wherever it runs vertically. When many lines enter one row from the
same side, as with a users table that 25 foreign keys point at, they all funnel through the gap next
to it. Size that gap for them:

```
gap ≈ 40 + 8 × (lines that pass through it)
```

The VisitCA accounts module needed `gap: 260` between `AppUser` (25 incoming lines) and
`PartnerProfile` (12). Booking needed 160 and catalogue 130; everything else used the default 96.
`groupGap` (between modules) defaults to 150, enough for about 14 parallel lanes.

## Reading check()

```js
await ERDiagram.instances[0].check()
// { tables, lines, size, routeMs, avgBends, failedRoutes, throughTables, throughHeaders, diagonal,
//   overlaps, overlapHotspots, overlapExamples, throughExamples }
```

| Metric | Healthy | When it isn't |
|---|---|---|
| `failedRoutes` | `[]` | The router hit its search limit and drew a fallback path, which can cross tables. Move the two modules closer or increase `groupGap`. |
| `throughTables` | 0 | Only happens with failed routes. |
| `throughHeaders` | 0 | Only happens with failed routes. |
| `diagonal` | 0 | Report it; the engine converts any slant into a square jog. |
| `overlaps` | 0 | Two lines with different targets share more than 16 px of track. `overlapHotspots` names the group (or "between groups") where it happens. Widen that group's `gap`, or `groupGap`. |
| `avgBends` | 3 to 5 | Above 6 usually means modules that talk to each other are far apart. |
| `routeMs` | under 1500 | The canvas is very large; reduce gaps or rebalance the grid. |

Lines that end on the same key row may share their last stretch; that is not counted as an overlap.
