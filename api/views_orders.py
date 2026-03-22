from datetime import datetime

from django.db import transaction

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import (
    OrderNotFoundException, CustomerNotFoundException,
    BookNotFoundException, InsufficientStockException,
)
from .models import Book, Customer, Order, OrderDetail
from .pagination import paginate_queryset
from .serializers import OrderWriteSerializer
from .views_customers import _serialize_orders


class OrderListCreateView(APIView):
    """GET /api/orders  |  POST /api/orders"""

    def get(self, request):
        qs = Order.objects.select_related('customer').prefetch_related('items')
        from_date = request.query_params.get('from')
        to_date = request.query_params.get('to')
        if from_date:
            qs = qs.filter(order_date__gte=from_date)
        if to_date:
            qs = qs.filter(order_date__lte=to_date)

        items, meta = paginate_queryset(qs, request)
        data = [
            {
                'orderId': o.id,
                'orderDate': str(o.order_date),
                'customerName': o.customer.name,
                'orderTotal': float(o.order_total),
            }
            for o in items
        ]
        return Response({'status': 'success', **meta, 'data': data})

    def post(self, request):
        ser = OrderWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        vd = ser.validated_data

        # Validate customer
        try:
            customer = Customer.objects.get(pk=vd['customerId'])
        except Customer.DoesNotExist:
            raise CustomerNotFoundException(f'No customer found with ID: {vd["customerId"]}')

        # Validate books and stock in one pass
        book_items = []
        for item in vd['items']:
            try:
                book = Book.objects.get(pk=item['bookId'])
            except Book.DoesNotExist:
                raise BookNotFoundException(f'No book found with ID: {item["bookId"]}')

            qty = item['quantityOrdered']
            if book.stock_quantity < qty:
                raise InsufficientStockException(
                    f'Requested {qty} copies of {book.title} but only {book.stock_quantity} in stock.'
                )
            book_items.append((book, qty))

        # Atomic transaction: create order + details + deduct stock
        with transaction.atomic():
            order = Order.objects.create(customer=customer, order_date=vd['orderDate'])
            details = []
            for book, qty in book_items:
                detail = OrderDetail.objects.create(
                    order=order,
                    book=book,
                    quantity_ordered=qty,
                    price_at_time_of_order=book.price,
                )
                book.stock_quantity -= qty
                book.save()
                details.append(detail)

        items_data = [
            {
                'bookId': d.book.id,
                'title': d.book.title,
                'quantityOrdered': d.quantity_ordered,
                'priceAtTimeOfOrder': float(d.price_at_time_of_order),
                'subtotal': float(d.subtotal),
            }
            for d in details
        ]
        order_total = sum(i['subtotal'] for i in items_data)

        return Response({
            'status': 'success',
            'message': 'Order placed successfully',
            'data': {
                'orderId': order.id,
                'orderDate': str(order.order_date),
                'customerId': customer.id,
                'orderTotal': order_total,
                'items': items_data,
            },
        }, status=status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    """GET /api/orders/{orderId}  |  DELETE /api/orders/{orderId}"""

    def _get_order(self, order_id):
        try:
            return Order.objects.select_related('customer').prefetch_related('items__book__author').get(pk=order_id)
        except Order.DoesNotExist:
            raise OrderNotFoundException(f'No order found with ID: {order_id}')

    def get(self, request, order_id):
        order = self._get_order(order_id)
        items_data = [
            {
                'detailId': item.id,
                'book': {
                    'bookId': item.book.id,
                    'title': item.book.title,
                    'author': item.book.author.author_name,
                },
                'quantityOrdered': item.quantity_ordered,
                'priceAtTimeOfOrder': float(item.price_at_time_of_order),
                'subtotal': float(item.subtotal),
            }
            for item in order.items.all()
        ]
        return Response({
            'status': 'success',
            'data': {
                'orderId': order.id,
                'orderDate': str(order.order_date),
                'customer': {
                    'customerId': order.customer.id,
                    'name': order.customer.name,
                    'email': order.customer.email,
                    'city': order.customer.city,
                },
                'items': items_data,
                'orderTotal': float(order.order_total),
            },
        })

    def delete(self, request, order_id):
        order = self._get_order(order_id)

        with transaction.atomic():
            for item in order.items.all():
                item.book.stock_quantity += item.quantity_ordered
                item.book.save()
            order.delete()

        return Response({'status': 'success', 'message': f'Order {order_id} cancelled. Stock quantities restored.'})


class OrdersByDateRangeView(APIView):
    """GET /api/orders/by-date-range?from=&to="""

    def get(self, request):
        from_date = request.query_params.get('from')
        to_date = request.query_params.get('to')

        qs = Order.objects.select_related('customer')
        if from_date:
            qs = qs.filter(order_date__gte=from_date)
        if to_date:
            qs = qs.filter(order_date__lte=to_date)

        orders = list(qs)
        data = [
            {
                'orderId': o.id,
                'orderDate': str(o.order_date),
                'customerName': o.customer.name,
                'orderTotal': float(o.order_total),
            }
            for o in orders
        ]
        total_revenue = sum(d['orderTotal'] for d in data)

        return Response({
            'status': 'success',
            'period': {'from': from_date, 'to': to_date},
            'totalOrders': len(data),
            'totalRevenue': total_revenue,
            'data': data,
        })


class OrdersByCustomerView(APIView):
    """GET /api/orders/customer/{customerId}"""

    def get(self, request, customer_id):
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            raise CustomerNotFoundException(f'No customer found with ID: {customer_id}')

        orders = Order.objects.prefetch_related('items__book').filter(customer=customer)
        orders_data = _serialize_orders(orders)

        return Response({
            'status': 'success',
            'customerId': customer.id,
            'customerName': customer.name,
            'totalOrders': len(orders_data),
            'data': orders_data,
        })


class OrderInvoiceView(APIView):
    """GET /api/orders/{orderId}/invoice"""

    def get(self, request, order_id):
        try:
            order = Order.objects.select_related('customer').prefetch_related('items__book').get(pk=order_id)
        except Order.DoesNotExist:
            raise OrderNotFoundException(f'No order found with ID: {order_id}')

        items_data = [
            {
                'title': item.book.title,
                'qty': item.quantity_ordered,
                'unitPrice': float(item.price_at_time_of_order),
                'total': float(item.subtotal),
            }
            for item in order.items.all()
        ]
        sub_total = float(order.order_total)
        invoice_number = f'KG-INV-{order.id:05d}'

        return Response({
            'status': 'success',
            'invoice': {
                'invoiceNumber': invoice_number,
                'orderId': order.id,
                'orderDate': str(order.order_date),
                'billedTo': {
                    'name': order.customer.name,
                    'email': order.customer.email,
                    'city': order.customer.city,
                },
                'items': items_data,
                'subTotal': sub_total,
                'tax': 0.00,
                'grandTotal': sub_total,
                'generatedAt': datetime.now().isoformat(),
            },
        })
