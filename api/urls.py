from django.urls import path

from .views_books import (
    BookListCreateView,
    BookDetailView,
    BooksByGenreView,
    BooksByAuthorView,
    BooksPriceRangeView,
    BooksBestsellersView,
    BooksNeverOrderedView,
)
from .views_authors import AuthorListCreateView, AuthorDetailView
from .views_genres import GenreListCreateView, GenreDeleteView
from .views_customers import (
    CustomerRegisterView,
    CustomerListView,
    CustomerTopSpendersView,
    CustomerDetailView,
    CustomerOrderHistoryView,
)
from .views_orders import (
    OrderListCreateView,
    OrderDetailView,
    OrdersByDateRangeView,
    OrdersByCustomerView,
    OrderInvoiceView,
)
from .views_inventory import InventoryListView, InventoryLowStockView, InventoryRestockView
from .views_reports import (
    RevenueView,
    RevenueByGenreView,
    RevenueByAuthorView,
    ReportsBestsellersView,
    CustomerWithMostOrdersView,
    InactiveCustomersView,
)
from .views_search import GlobalSearchView

urlpatterns = [
    # ── Books (Domain 1) ───────────────────────────────────────────────────────
    path('books/', BookListCreateView.as_view(), name='book-list-create'),
    path('books/by-genre/<int:genre_id>/', BooksByGenreView.as_view(), name='books-by-genre'),
    path('books/by-author/<int:author_id>/', BooksByAuthorView.as_view(), name='books-by-author'),
    path('books/price-range/', BooksPriceRangeView.as_view(), name='books-price-range'),
    path('books/bestsellers/', BooksBestsellersView.as_view(), name='books-bestsellers'),
    path('books/never-ordered/', BooksNeverOrderedView.as_view(), name='books-never-ordered'),
    path('books/<int:book_id>/', BookDetailView.as_view(), name='book-detail'),

    # ── Authors (Domain 2) ─────────────────────────────────────────────────────
    path('authors/', AuthorListCreateView.as_view(), name='author-list-create'),
    path('authors/<int:author_id>/', AuthorDetailView.as_view(), name='author-detail'),

    # ── Genres (Domain 3) ──────────────────────────────────────────────────────
    path('genres/', GenreListCreateView.as_view(), name='genre-list-create'),
    path('genres/<int:genre_id>/', GenreDeleteView.as_view(), name='genre-delete'),

    # ── Customers (Domain 4) ───────────────────────────────────────────────────
    path('customers/register/', CustomerRegisterView.as_view(), name='customer-register'),
    path('customers/top-spenders/', CustomerTopSpendersView.as_view(), name='customer-top-spenders'),
    path('customers/', CustomerListView.as_view(), name='customer-list'),
    path('customers/<int:customer_id>/', CustomerDetailView.as_view(), name='customer-detail'),
    path('customers/<int:customer_id>/orders/', CustomerOrderHistoryView.as_view(), name='customer-orders'),

    # ── Orders (Domain 5) ──────────────────────────────────────────────────────
    path('orders/', OrderListCreateView.as_view(), name='order-list-create'),
    path('orders/by-date-range/', OrdersByDateRangeView.as_view(), name='orders-by-date-range'),
    path('orders/customer/<int:customer_id>/', OrdersByCustomerView.as_view(), name='orders-by-customer'),
    path('orders/<int:order_id>/invoice/', OrderInvoiceView.as_view(), name='order-invoice'),
    path('orders/<int:order_id>/', OrderDetailView.as_view(), name='order-detail'),

    # ── Inventory (Domain 6) ───────────────────────────────────────────────────
    path('inventory/', InventoryListView.as_view(), name='inventory-list'),
    path('inventory/low-stock/', InventoryLowStockView.as_view(), name='inventory-low-stock'),
    path('inventory/<int:book_id>/restock/', InventoryRestockView.as_view(), name='inventory-restock'),

    # ── Reports (Domain 7) ─────────────────────────────────────────────────────
    path('reports/revenue/', RevenueView.as_view(), name='report-revenue'),
    path('reports/revenue-by-genre/', RevenueByGenreView.as_view(), name='report-revenue-by-genre'),
    path('reports/revenue-by-author/', RevenueByAuthorView.as_view(), name='report-revenue-by-author'),
    path('reports/bestsellers/', ReportsBestsellersView.as_view(), name='report-bestsellers'),
    path('reports/customer-with-most-orders/', CustomerWithMostOrdersView.as_view(), name='report-top-customer'),
    path('reports/inactive-customers/', InactiveCustomersView.as_view(), name='report-inactive-customers'),

    # ── Search (Domain 8) ──────────────────────────────────────────────────────
    path('search/', GlobalSearchView.as_view(), name='global-search'),
]
