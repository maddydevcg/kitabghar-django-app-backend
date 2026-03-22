# KitabGhar REST API — Django + SQLite3

A complete implementation of the **KitabGhar Bookstore REST API** spec using:
- **Python / Django 4.2**
- **Django REST Framework 3.14**
- **SQLite3** (zero-config database)

## Project Structure

```
kitabghar/
├── manage.py
├── requirements.txt
├── db.sqlite3               ← auto-created on first migrate
├── kitabghar/               ← Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── api/                     ← Single Django app
    ├── models.py            ← Author, Genre, Book, Customer, Order, OrderDetail
    ├── serializers.py
    ├── exceptions.py        ← Custom error codes + envelope handler
    ├── pagination.py        ← page/size/sort/order helpers
    ├── urls.py              ← All 41 route registrations
    ├── views_books.py       ← Domain 1: Book Catalog (10 endpoints)
    ├── views_authors.py     ← Domain 2: Authors (5 endpoints)
    ├── views_genres.py      ← Domain 3: Genres (3 endpoints)
    ├── views_customers.py   ← Domain 4: Customers (5 endpoints)
    ├── views_orders.py      ← Domain 5: Orders (7 endpoints)
    ├── views_inventory.py   ← Domain 6: Inventory (3 endpoints)
    ├── views_reports.py     ← Domain 7: Reports (6 endpoints)
    ├── views_search.py      ← Domain 8: Global Search (1 endpoint)
    └── management/
        └── commands/
            └── seed_data.py ← Sample data loader
```

## Quick Start

### 1. Install dependencies

```bash
pip install django djangorestframework
```

### 2. Run migrations (creates db.sqlite3 automatically)

```bash
cd kitabghar
python manage.py migrate
```

### 3. Seed sample data (optional but recommended)

```bash
python manage.py seed_data
```

### 4. Start the development server

```bash
python manage.py runserver 8080
```

The API is now live at **http://localhost:8080**

---

## All 41 Endpoints

### Domain 1 — Book Catalog (`/api/books/`)

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/books/` | List all books (filterable: genre, minPrice, maxPrice, page, size, sort, order) |
| POST | `/api/books/` | Add a new book |
| GET | `/api/books/{bookId}/` | Get full book details |
| PUT | `/api/books/{bookId}/` | Update book |
| DELETE | `/api/books/{bookId}/` | Delete book |
| GET | `/api/books/by-genre/{genreId}/` | All books in a genre |
| GET | `/api/books/by-author/{authorId}/` | All books by an author |
| GET | `/api/books/price-range/` | Filter by `?min=&max=` |
| GET | `/api/books/bestsellers/` | Top N most-ordered (`?limit=5`) |
| GET | `/api/books/never-ordered/` | Books never in any order |

### Domain 2 — Authors (`/api/authors/`)

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/authors/` | List all authors with book count |
| POST | `/api/authors/` | Register new author |
| GET | `/api/authors/{authorId}/` | Author profile + books + avg price |
| PUT | `/api/authors/{authorId}/` | Update author |
| DELETE | `/api/authors/{authorId}/` | Delete (blocked if books linked) |

### Domain 3 — Genres (`/api/genres/`)

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/genres/` | List genres with book count |
| POST | `/api/genres/` | Add new genre |
| DELETE | `/api/genres/{genreId}/` | Delete (blocked if books linked) |

### Domain 4 — Customers (`/api/customers/`)

| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api/customers/register/` | Register customer |
| GET | `/api/customers/` | List customers (`?city=`) |
| GET | `/api/customers/top-spenders/` | Top by spend (`?limit=5`) |
| GET | `/api/customers/{customerId}/` | Profile + order summary |
| PUT | `/api/customers/{customerId}/` | Update profile |
| GET | `/api/customers/{customerId}/orders/` | Full order history |

### Domain 5 — Orders (`/api/orders/`)

| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api/orders/` | Place order (atomic stock check) |
| GET | `/api/orders/` | List all (`?from=&to=`) |
| GET | `/api/orders/by-date-range/` | Orders in date window |
| GET | `/api/orders/customer/{customerId}/` | Orders for a customer |
| GET | `/api/orders/{orderId}/` | Full order detail |
| GET | `/api/orders/{orderId}/invoice/` | Invoice JSON |
| DELETE | `/api/orders/{orderId}/` | Cancel + restore stock |

### Domain 6 — Inventory (`/api/inventory/`)

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/inventory/` | Complete stock overview |
| GET | `/api/inventory/low-stock/` | Below threshold (`?threshold=25`) |
| PATCH | `/api/inventory/{bookId}/restock/` | Add stock delta |

### Domain 7 — Reports (`/api/reports/`)

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/reports/revenue/` | Total revenue (`?from=&to=`) |
| GET | `/api/reports/revenue-by-genre/` | Revenue per genre |
| GET | `/api/reports/revenue-by-author/` | Revenue per author |
| GET | `/api/reports/bestsellers/` | Top books by qty sold |
| GET | `/api/reports/customer-with-most-orders/` | VIP customer |
| GET | `/api/reports/inactive-customers/` | Inactive (`?months=6`) |

### Domain 8 — Search (`/api/search/`)

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/search/` | Cross-entity search (`?q=&type=all|books|authors`) |

---

## Sample Requests

```bash
# List books with price filter
curl "http://localhost:8080/api/books/?minPrice=100&maxPrice=400"

# Place an order
curl -X POST http://localhost:8080/api/orders/ \
  -H "Content-Type: application/json" \
  -d '{"customerId":1,"orderDate":"2024-06-10","items":[{"bookId":1,"quantityOrdered":2}]}'

# Restock a book
curl -X PATCH http://localhost:8080/api/inventory/3/restock/ \
  -H "Content-Type: application/json" \
  -d '{"additionalQuantity":50,"reason":"New shipment from publisher"}'

# Search
curl "http://localhost:8080/api/search/?q=chetan&type=all"
```

## Response Envelope

Every response follows the spec's standard envelope:

**Success:**
```json
{ "status": "success", "data": { ... } }
```

**Error:**
```json
{
  "status": "error",
  "code": "BOOK_NOT_FOUND",
  "message": "No book found with ID: 99",
  "timestamp": "2024-06-10T14:30:00"
}
```

## Error Codes

| Code | HTTP | Meaning |
|------|------|---------|
| `BOOK_NOT_FOUND` | 404 | No book for given ID |
| `AUTHOR_NOT_FOUND` | 404 | No author for given ID |
| `CUSTOMER_NOT_FOUND` | 404 | No customer for given ID |
| `ORDER_NOT_FOUND` | 404 | No order for given ID |
| `GENRE_NOT_FOUND` | 404 | No genre for given ID |
| `INSUFFICIENT_STOCK` | 409 | Quantity exceeds available stock |
| `AUTHOR_HAS_BOOKS` | 409 | Cannot delete author with linked books |
| `GENRE_HAS_BOOKS` | 409 | Cannot delete genre with linked books |
| `DUPLICATE_EMAIL` | 409 | Email already registered |
| `VALIDATION_ERROR` | 400 | Request body failed validation |
