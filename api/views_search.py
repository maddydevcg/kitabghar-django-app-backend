from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Author, Book


class GlobalSearchView(APIView):
    """GET /api/search?q=&type=all|books|authors"""

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        search_type = request.query_params.get('type', 'all')

        books_data = []
        authors_data = []

        if search_type in ('all', 'books') and q:
            books = Book.objects.select_related('author', 'genre').filter(title__icontains=q)
            # Also include books whose author name matches
            if search_type == 'all':
                books = books | Book.objects.select_related('author', 'genre').filter(author__author_name__icontains=q)
                books = books.distinct()

            books_data = [
                {
                    'bookId': b.id,
                    'title': b.title,
                    'price': float(b.price),
                    'author': b.author.author_name,
                    'genre': b.genre.genre_name,
                }
                for b in books
            ]

        if search_type in ('all', 'authors') and q:
            from django.db.models import Count
            authors = Author.objects.annotate(totalBooks=Count('books')).filter(author_name__icontains=q)
            authors_data = [
                {
                    'authorId': a.id,
                    'authorName': a.author_name,
                    'totalBooks': a.totalBooks,
                }
                for a in authors
            ]

        total_hits = len(books_data) + len(authors_data)

        return Response({
            'status': 'success',
            'query': q,
            'results': {
                'books': books_data,
                'authors': authors_data,
                'totalHits': total_hits,
            },
        })
