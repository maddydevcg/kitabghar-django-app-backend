from datetime import datetime

from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import BookNotFoundException
from .models import Book
from .serializers import RestockSerializer


def _stock_status(qty):
    if qty == 0:
        return 'OUT_OF_STOCK'
    if qty <= 25:
        return 'LOW_STOCK'
    return 'IN_STOCK'


class InventoryListView(APIView):
    """GET /api/inventory"""

    def get(self, request):
        books = Book.objects.select_related('author').all()
        data = [
            {
                'bookId': b.id,
                'title': b.title,
                'stockQuantity': b.stock_quantity,
                'stockStatus': _stock_status(b.stock_quantity),
            }
            for b in books
        ]
        return Response({'status': 'success', 'data': data})


class InventoryLowStockView(APIView):
    """GET /api/inventory/low-stock?threshold=25"""

    def get(self, request):
        threshold = int(request.query_params.get('threshold', 25))
        books = Book.objects.select_related('author').filter(stock_quantity__lte=threshold)
        data = [
            {
                'bookId': b.id,
                'title': b.title,
                'author': b.author.author_name,
                'stockQuantity': b.stock_quantity,
                'message': 'Stock below threshold. Reorder recommended.',
            }
            for b in books
        ]
        return Response({
            'status': 'success',
            'threshold': threshold,
            'alertCount': len(data),
            'data': data,
        })


class InventoryRestockView(APIView):
    """PATCH /api/inventory/{bookId}/restock"""

    def patch(self, request, book_id):
        try:
            book = Book.objects.get(pk=book_id)
        except Book.DoesNotExist:
            raise BookNotFoundException(f'No book found with ID: {book_id}')

        ser = RestockSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        vd = ser.validated_data

        previous_stock = book.stock_quantity
        additional = vd['additionalQuantity']
        book.stock_quantity += additional
        book.save()

        return Response({
            'status': 'success',
            'message': f'Stock updated for {book.title}',
            'data': {
                'bookId': book.id,
                'previousStock': previous_stock,
                'additionalQuantity': additional,
                'newStock': book.stock_quantity,
                'updatedAt': datetime.now().isoformat(),
            },
        })
