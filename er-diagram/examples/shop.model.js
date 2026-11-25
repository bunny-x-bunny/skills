// Small example: an online shop, four modules on a 2 × 2 grid. Shows every feature of the model format:
// kinds, statuses and phases, phase tags on fields, alternate (Russian) names, summaries, field
// descriptions, source text quoted from the code (Django help_text here), a self-reference, a link table
// with a composite key, and identifying vs non-identifying relationships.
var MODEL = {
  title: "Shop data model",
  altLang: "ru",
  sourceLabel: "`help_text` on {entity}",
  layout: { colGap: 96, groupGap: 140 },
  entities: {
    Category: { kind: "ref", status: "current", alt: "Категория", summary: "Product category tree used for navigation and filters.", fields: [
      ["id", "bigint", "P"],
      ["parent_id", "bigint", "F", "", "Parent category; empty for top-level categories.", "Parent category"],
      ["slug", "varchar", "U", "", "", "URL slug"],
      ["name", "varchar", "", "", "Name shown in menus and breadcrumbs.", "Category name"]] },
    Product: { kind: "core", status: "changed", alt: "Товар", summary: "Something the shop sells, with its price and stock.", fields: [
      ["id", "bigint", "P"],
      ["category_id", "bigint", "F", "", "Category the product is listed in.", "Category"],
      ["sku", "varchar", "U", "", "Stock-keeping unit from the warehouse system.", "SKU"],
      ["title", "varchar", "", "", "Product name shown on cards.", "Title"],
      ["price", "numeric", "I", "", "Current price in EUR; indexed for the price filter.", "Price, EUR"],
      ["stock", "int", "D", "", "Units in stock, synced from the warehouse every 5 minutes.", "Units in stock"],
      ["rating", "numeric", "D", "P2", "Average of approved reviews."],
      ["deleted_at", "timestamptz", "", "P1"]] },
    ProductImage: { kind: "dep", status: "current", alt: "Фото товара", summary: "Photos of a product, in gallery order.", fields: [
      ["id", "bigint", "P"],
      ["product_id", "bigint", "F", "", "Product the photo belongs to.", "Product"],
      ["url", "text", "", "", "Image address on the CDN.", "Image URL"],
      ["position", "int", "", "", "", "Position in gallery"]] },
    Customer: { kind: "core", status: "current", alt: "Покупатель", summary: "A person who can sign in, order and write reviews.", fields: [
      ["id", "bigint", "P"],
      ["email", "varchar", "U", "", "Sign-in email; unique.", "Email"],
      ["full_name", "varchar", "", "", "Name printed on invoices.", "Full name"],
      ["created_at", "timestamptz"]] },
    Address: { kind: "dep", status: "current", alt: "Адрес доставки", summary: "A delivery address a customer saved.", fields: [
      ["id", "bigint", "P"],
      ["customer_id", "bigint", "F", "", "Owner of the address.", "Customer"],
      ["line1", "varchar", "", "", "Street and house number.", "Address line"],
      ["city", "varchar", "", "", "", "City"],
      ["country", "char(2)", "", "", "ISO 3166 country code.", "Country"]] },
    Wishlist: { kind: "link", status: "new", phase: "P2", alt: "Избранное", summary: "Products a customer saved for later.", fields: [
      ["customer_id", "bigint", "PF", "", "Customer who saved the product."],
      ["product_id", "bigint", "PF", "", "Saved product."],
      ["created_at", "timestamptz"]] },
    Order: { kind: "core", status: "changed", alt: "Заказ", summary: "A customer's order with its status and total.", fields: [
      ["id", "bigint", "P"],
      ["customer_id", "bigint", "F", "", "Who placed the order.", "Customer"],
      ["address_id", "bigint", "F", "", "Delivery address chosen at checkout.", "Delivery address"],
      ["status", "varchar", "I", "", "pending, paid, shipped, delivered or cancelled.", "Order status"],
      ["total", "numeric", "", "", "Order total in EUR.", "Total, EUR"],
      ["promo_code", "varchar", "", "P1", "Promo code applied at checkout."],
      ["created_at", "timestamptz", "I"]] },
    OrderLine: { kind: "dep", status: "current", alt: "Строка заказа", summary: "One product in an order, with quantity and the price paid.", fields: [
      ["id", "bigint", "P"],
      ["order_id", "bigint", "F", "", "Order the line belongs to.", "Order"],
      ["product_id", "bigint", "F", "", "Product bought.", "Product"],
      ["quantity", "int", "", "", "", "Quantity"],
      ["unit_price", "numeric", "", "", "Price per unit at checkout, EUR, so later price changes don't alter the order.", "Unit price"]] },
    Payment: { kind: "log", status: "current", alt: "Платёж", summary: "A payment or refund recorded against an order.", fields: [
      ["id", "bigint", "P"],
      ["order_id", "bigint", "F", "", "Order paid.", "Order"],
      ["amount", "numeric", "", "", "Amount in EUR; negative for refunds.", "Amount"],
      ["provider_ref", "varchar", "U", "", "Reference from the payment provider, used to match webhooks.", "Provider reference"],
      ["created_at", "timestamptz"]] },
    Shipment: { kind: "dep", status: "new", phase: "P1", alt: "Отправка", summary: "A parcel sent for an order, with its tracking number.", fields: [
      ["id", "bigint", "P"],
      ["order_id", "bigint", "F", "", "Order shipped."],
      ["carrier", "varchar", "", "", "Delivery company."],
      ["tracking_code", "varchar", "U", "", "Carrier tracking number."],
      ["shipped_at", "timestamptz", "", "", "When the parcel left the warehouse."]] },
    Review: { kind: "core", status: "new", phase: "P2", alt: "Отзыв", summary: "A customer's rating and comment on a product, shown after moderation.", fields: [
      ["id", "bigint", "P"],
      ["product_id", "bigint", "F", "", "Product reviewed."],
      ["customer_id", "bigint", "F", "", "Author."],
      ["order_line_id", "bigint", "F", "", "Purchase that proves the customer bought the product."],
      ["rating", "smallint", "", "", "1 to 5."],
      ["body", "text", "", "", "Review text."],
      ["approved", "bool", "I", "", "Shown once a moderator approves it."]] }
  },
  // [child, child FK field, parent, parent key, parent side ("1" | "01"), child side ("0n" | "1n"), identifying, label]
  relations: [
    ["Category", "parent_id", "Category", "id", "01", "0n", false, "parent"],
    ["Product", "category_id", "Category", "id", "1", "0n", false, "lists"],
    ["ProductImage", "product_id", "Product", "id", "1", "0n", false, "shows"],
    ["Address", "customer_id", "Customer", "id", "1", "0n", false, "saves"],
    ["Wishlist", "customer_id", "Customer", "id", "1", "0n", true, "saves"],
    ["Wishlist", "product_id", "Product", "id", "1", "0n", true, "saved in"],
    ["Order", "customer_id", "Customer", "id", "1", "0n", false, "places"],
    ["Order", "address_id", "Address", "id", "01", "0n", false, "ships to"],
    ["OrderLine", "order_id", "Order", "id", "1", "1n", false, "contains"],
    ["OrderLine", "product_id", "Product", "id", "1", "0n", false, "sells"],
    ["Payment", "order_id", "Order", "id", "1", "0n", false, "pays"],
    ["Shipment", "order_id", "Order", "id", "1", "0n", false, "ships"],
    ["Review", "product_id", "Product", "id", "1", "0n", false, "rates"],
    ["Review", "customer_id", "Customer", "id", "1", "0n", false, "writes"],
    ["Review", "order_line_id", "OrderLine", "id", "01", "0n", false, "proves"]
  ],
  // at: [grid column, grid row]; cols: columns of tables inside the group, left to right
  groups: [
    { id: "catalog", short: "Catalog", title: "Catalog", note: "What the shop sells", at: [0, 0], cols: [["Category"], ["Product", "ProductImage"]] },
    { id: "customers", short: "Customers", title: "Customers", note: "Who buys, and where it goes", at: [1, 0], cols: [["Customer"], ["Address", "Wishlist"]] },
    { id: "reviews", short: "Reviews", title: "Reviews", note: "What customers think", at: [0, 1], cols: [["Review"]] },
    { id: "orders", short: "Orders", title: "Orders and payments", note: "From checkout to delivery", at: [1, 1], cols: [["Order"], ["OrderLine", "Payment", "Shipment"]] }
  ]
};
