from django.db.models import Count

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import GenreNotFoundException, GenreHasBooksException
from .models import Genre
from .serializers import GenreWriteSerializer


class GenreListCreateView(APIView):
    """GET /api/genres  |  POST /api/genres"""

    def get(self, request):
        genres = Genre.objects.annotate(bookCount=Count('books')).order_by('genre_name')
        data = [
            {
                'genreId': g.id,
                'genreName': g.genre_name,
                'bookCount': g.bookCount,
            }
            for g in genres
        ]
        return Response({'status': 'success', 'data': data})

    def post(self, request):
        ser = GenreWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        genre = Genre.objects.create(genre_name=ser.validated_data['genre_name'])
        return Response({
            'status': 'success',
            'data': {'genreId': genre.id, 'genreName': genre.genre_name},
        }, status=status.HTTP_201_CREATED)


class GenreDeleteView(APIView):
    """DELETE /api/genres/{genreId}"""

    def delete(self, request, genre_id):
        try:
            genre = Genre.objects.get(pk=genre_id)
        except Genre.DoesNotExist:
            raise GenreNotFoundException(f'No genre found with ID: {genre_id}')

        if genre.books.exists():
            raise GenreHasBooksException()

        name = genre.genre_name
        genre.delete()
        return Response({'status': 'success', 'message': f'Genre {name} deleted successfully'})
