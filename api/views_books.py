from datetime import datetime
from decimal import Decimal

from django.db.models import Sum, Count, Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import BookNotFoundException
from .models import Author, Book, Genre, OrderDetail
from .pagination import paginate_queryset
from .serializers import BookDetailSerializer, BookListSerializer, BookWriteSerializer


class BookListCreateView(APIView):
    """GET /api/books  |  POST /api/books"""

    def get(self, request):
        qs = Book.objects.select_related('author', 'genre').all()

        genre_id = request.query_params.get('genre')
        min_price = request.query_params.get('minPrice')
        max_price = request.query_params.get('maxPrice')

        if genre_id:
            qs = qs.filter(genre_id=genre_id)
        if min_price:
            qs = qs.filter(price__gte=Decimal(min_price))
        if max_price:
            qs = qs.filter(price__lte=Decimal(max_price))

        items, meta = paginate_queryset(qs, request)
        data = BookListSerializer(items, many=True).data
        return Response({'status': 'success', **meta, 'data': data})

    def post(self, request):
        ser = BookWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        vd = ser.validated_data

        book = Book.objects.create(
            title=vd['title'],
            price=vd['price'],
            stock_quantity=vd.get('stock_quantity', 0),
            author_id=request.data['authorId'],
            genre_id=request.data['genreId'],
        )
        return Response({
            'status': 'success',
            'message': 'Book added to catalog successfully',
            'data': {
                'bookId': book.id,
                'title': book.title,
                'price': book.price,
                'stockQuantity': book.stock_quantity,
                'authorId': book.author_id,
                'genreId': book.genre_id,
            },
        }, status=status.HTTP_201_CREATED)


class BookDetailView(APIView):
    """GET /api/books/{bookId}  |  PUT /api/books/{bookId}  |  DELETE /api/books/{bookId}"""

    def _get_book(self, book_id):
        try:
            return Book.objects.select_related('author', 'genre').get(pk=book_id)
        except Book.DoesNotExist:
            raise BookNotFoundException(f'No book found with ID: {book_id}')

    def get(self, request, book_id):
        book = self._get_book(book_id)
        data = BookDetailSerializer(book).data
        return Response({'status': 'success', 'data': data})

    def put(self, request, book_id):
        book = self._get_book(book_id)
        ser = BookWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        vd = ser.validated_data

        book.title = vd['title']
        book.price = vd['price']
        book.stock_quantity = vd.get('stock_quantity', book.stock_quantity)
        book.author_id = request.data['authorId']
        book.genre_id = request.data['genreId']
        book.save()

        return Response({
            'status': 'success',
            'message': 'Book updated successfully',
            'data': {
                'bookId': book.id,
                'price': book.price,
                'stockQuantity': book.stock_quantity,
            },
        })

    def delete(self, request, book_id):
        book = self._get_book(book_id)
        book.delete()
        return Response({'status': 'success', 'message': f'Book with ID {book_id} removed from catalog'})


class BooksByGenreView(APIView):
    """GET /api/books/by-genre/{genreId}"""

    def get(self, request, genre_id):
        try:
            genre = Genre.objects.get(pk=genre_id)
        except Genre.DoesNotExist:
            from .exceptions import GenreNotFoundException
            raise GenreNotFoundException(f'No genre found with ID: {genre_id}')

        books = Book.objects.filter(genre=genre).select_related('author', 'genre')
        data = [
            {
                'bookId': b.id,
                'title': b.title,
                'price': b.price,
                'author': b.author.author_name,
            }
            for b in books
        ]
        return Response({'status': 'success', 'genre': genre.genre_name, 'count': len(data), 'data': data})


class BooksByAuthorView(APIView):
    """GET /api/books/by-author/{authorId}"""

    def get(self, request, author_id):
        try:
            author = Author.objects.get(pk=author_id)
        except Author.DoesNotExist:
            from .exceptions import AuthorNotFoundException
            raise AuthorNotFoundException(f'No author found with ID: {author_id}')

        books = Book.objects.filter(author=author).select_related('genre')
        data = [
            {
                'bookId': b.id,
                'title': b.title,
                'price': b.price,
                'genre': b.genre.genre_name,
            }
            for b in books
        ]
        return Response({'status': 'success', 'author': author.author_name, 'count': len(data), 'data': data})


class BooksPriceRangeView(APIView):
    """GET /api/books/price-range?min=&max="""

    def get(self, request):
        min_price = request.query_params.get('min', 0)
        max_price = request.query_params.get('max', 999999)
        books = Book.objects.filter(price__gte=min_price, price__lte=max_price)
        data = [{'bookId': b.id, 'title': b.title, 'price': b.price} for b in books]
        return Response({
            'status': 'success',
            'minPrice': float(min_price),
            'maxPrice': float(max_price),
            'count': len(data),
            'data': data,
        })


class BooksBestsellersView(APIView):
    """GET /api/books/bestsellers?limit=5"""

    def get(self, request):
        limit = int(request.query_params.get('limit', 5))
        results = (
            OrderDetail.objects
            .values('book__id', 'book__title', 'book__price', 'book__author__author_name')
            .annotate(totalQuantitySold=Sum('quantity_ordered'))
            .order_by('-totalQuantitySold')[:limit]
        )
        data = [
            {
                'bookId': r['book__id'],
                'title': r['book__title'],
                'author': r['book__author__author_name'],
                'totalQuantitySold': r['totalQuantitySold'],
                'price': r['book__price'],
            }
            for r in results
        ]
        return Response({'status': 'success', 'data': data})


class BooksNeverOrderedView(APIView):
    """GET /api/books/never-ordered"""

    def get(self, request):
        ordered_ids = OrderDetail.objects.values_list('book_id', flat=True).distinct()
        books = Book.objects.exclude(id__in=ordered_ids)
        data = [{'bookId': b.id, 'title': b.title, 'price': b.price} for b in books]
        return Response({'status': 'success', 'count': len(data), 'data': data})
