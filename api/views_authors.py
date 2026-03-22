from django.db.models import Avg, Count

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import AuthorNotFoundException, AuthorHasBooksException
from .models import Author
from .serializers import AuthorWriteSerializer


class AuthorListCreateView(APIView):
    """GET /api/authors  |  POST /api/authors"""

    def get(self, request):
        authors = Author.objects.annotate(totalBooks=Count('books')).order_by('author_name')
        data = [
            {
                'authorId': a.id,
                'authorName': a.author_name,
                'totalBooks': a.totalBooks,
            }
            for a in authors
        ]
        return Response({'status': 'success', 'count': len(data), 'data': data})

    def post(self, request):
        ser = AuthorWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        author = Author.objects.create(
            author_name=ser.validated_data['author_name'],
            bio=ser.validated_data.get('bio', ''),
        )
        return Response({
            'status': 'success',
            'message': 'Author registered successfully',
            'data': {'authorId': author.id, 'authorName': author.author_name},
        }, status=status.HTTP_201_CREATED)


class AuthorDetailView(APIView):
    """GET /api/authors/{authorId}  |  PUT /api/authors/{authorId}  |  DELETE /api/authors/{authorId}"""

    def _get_author(self, author_id):
        try:
            return Author.objects.get(pk=author_id)
        except Author.DoesNotExist:
            raise AuthorNotFoundException(f'No author found with ID: {author_id}')

    def get(self, request, author_id):
        author = self._get_author(author_id)
        books = author.books.select_related('genre').all()
        avg_price = books.aggregate(avg=Avg('price'))['avg'] or 0

        books_data = [
            {
                'bookId': b.id,
                'title': b.title,
                'price': b.price,
                'genre': b.genre.genre_name,
            }
            for b in books
        ]
        return Response({
            'status': 'success',
            'data': {
                'authorId': author.id,
                'authorName': author.author_name,
                'bio': author.bio,
                'averageBookPrice': round(float(avg_price), 2),
                'books': books_data,
            },
        })

    def put(self, request, author_id):
        author = self._get_author(author_id)
        ser = AuthorWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        author.author_name = ser.validated_data['author_name']
        author.bio = ser.validated_data.get('bio', author.bio)
        author.save()
        return Response({
            'status': 'success',
            'message': 'Author updated',
            'data': {'authorId': author.id},
        })

    def delete(self, request, author_id):
        author = self._get_author(author_id)
        if author.books.exists():
            raise AuthorHasBooksException()
        author.delete()
        return Response({'status': 'success', 'message': f'Author with ID {author_id} deleted successfully'})
