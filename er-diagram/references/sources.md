# Pulling the schema out of code

Read the code yourself for structure (navigation properties and configuration classes rarely fit one
regex), and use these snippets to collect description text verbatim, because the hover cards quote it.

## EF Core / C#

Descriptions from `[Description("…")]` attributes, as `Entity|Property|Text` lines:

```sh
for f in Domain/Models/*.cs; do ent=$(basename "$f" .cs); awk -v E="$ent" '
/\[Description\(/ { d=$0; sub(/.*\[Description\(@?"/, "", d); sub(/"\)\].*$/, "", d); gsub(/\\"/, "\"", d); pend=d; next }
/^[[:space:]]*public / && /\{ *get/ { n=$0; sub(/[[:space:]]*\{.*/, "", n); k=split(n, a, " "); if (pend != "") print E "|" a[k] "|" pend; pend=""; next }
/^[[:space:]]*public / { pend="" }' "$f"; done
```

Also check XML doc comments (`/// <summary>`) and `[Comment("…")]` / `.HasComment("…")`.

Keys and indexes live in `IEntityTypeConfiguration<T>` classes or `OnModelCreating`:
`HasKey(...)` (primary keys, composite with `new { a, b }`), `HasIndex(...)` plus `.IsUnique()`,
`HasOne(...).WithMany(...).HasForeignKey(...)` and `.IsRequired()` / nullable navigation for
`"1"` vs `"01"`. `OwnsOne`/`OwnsMany`/`ToJson()` types are stored inside the owner: list them as
fields with the value-object name as the type, not as tables. ASP.NET Identity adds `AspNetUsers`
columns (Email, PasswordHash and so on) to the user class.

## Django

```sh
grep -nE "help_text=|verbose_name=|ForeignKey\(|OneToOneField\(|ManyToManyField\(|unique=True|db_index=True|class Meta|unique_together|indexes" */models.py
```

`help_text` is the source text. `ForeignKey(..., null=True)` is `"01"`. A `ManyToManyField` without
`through=` creates a hidden join table (`app_model_field`): draw it as a `link` table with two `PF`
fields.

## Prisma

`///` comments above a field or model are the source text. `@id`/`@@id` → `P`, `@unique`/`@@unique`
→ `U`, `@@index` → `I`, `@relation(fields: [x], references: [id])` gives the foreign key, and an
optional relation type (`User?`) means `"01"`.

## TypeORM / Sequelize

`@Column({ comment: "…" })` is the source text. `@PrimaryGeneratedColumn`/`@PrimaryColumn` → `P`,
`@Index()` → `I`, `@Unique` → `U`, `@ManyToOne(() => X, { nullable })` with `@JoinColumn`
gives the foreign key and its optionality.

## Rails

`db/schema.rb` lists tables, columns, `null: false`, indexes (`unique: true`) and `add_foreign_key`.
Comments come from `comment:` options when the team uses them.

## SQL databases

PostgreSQL column comments and foreign keys:

```sql
SELECT c.table_name, c.column_name, c.data_type, c.is_nullable,
       col_description((quote_ident(c.table_schema) || '.' || quote_ident(c.table_name))::regclass, c.ordinal_position) AS comment
FROM information_schema.columns c WHERE c.table_schema = 'public' ORDER BY c.table_name, c.ordinal_position;

SELECT tc.table_name, kcu.column_name, ccu.table_name AS parent, ccu.column_name AS parent_column
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY';
```

MySQL keeps comments in `information_schema.COLUMNS.COLUMN_COMMENT`.

## When there is no code

Model what the user describes, mark every field you inferred in its description ("assumed"), and say
so when you deliver. A diagram that looks authoritative but invents columns is worse than none.
