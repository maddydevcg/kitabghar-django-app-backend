from django.db.models import Sum, Count

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import CustomerNotFoundException, DuplicateEmailException
from .models import Customer, Order
from .pagination import paginate_queryset
from .serializers import CustomerWriteSerializer, CustomerUpdateSerializer


class CustomerRegisterView(APIView):
    """POST /api/customers/register"""

    def post(self, request):
        ser = CustomerWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        email = ser.validated_data['email']

        if Customer.objects.filter(email=email).exists():
            raise DuplicateEmailException()

        customer = Customer.objects.create(
            name=ser.validated_data['name'],
            email=email,
            city=ser.validated_data['city'],
            join_date=ser.validated_data['join_date'],
        )
        return Response({
            'status': 'success',
            'message': 'Customer registered successfully',
            'data': {
                'customerId': customer.id,
                'name': customer.name,
                'email': customer.email,
                'city': customer.city,
                'joinDate': str(customer.join_date),
            },
        }, status=status.HTTP_201_CREATED)


class CustomerListView(APIView):
    """GET /api/customers  — admin list, filterable by city"""

    def get(self, request):
        qs = Customer.objects.all()
        city = request.query_params.get('city')
        if city:
            qs = qs.filter(city__iexact=city)

        items, meta = paginate_queryset(qs, request)
        data = [
            {
                'customerId': c.id,
                'name': c.name,
                'email': c.email,
                'city': c.city,
            }
            for c in items
        ]
        return Response({'status': 'success', **meta, 'data': data})


class CustomerTopSpendersView(APIView):
    """GET /api/customers/top-spenders?limit=5"""

    def get(self, request):
        limit = int(request.query_params.get('limit', 5))
        customers = (
            Customer.objects
            .annotate(
                totalAmountSpent=Sum('orders__items__price_at_time_of_order'),
                totalOrders=Count('orders', distinct=True),
            )
            .order_by('-totalAmountSpent')[:limit]
        )
        data = [
            {
                'customerId': c.id,
                'name': c.name,
                'city': c.city,
                'totalAmountSpent': float(c.totalAmountSpent or 0),
                'totalOrders': c.totalOrders,
            }
            for c in customers
        ]
        return Response({'status': 'success', 'data': data})


class CustomerDetailView(APIView):
    """GET /api/customers/{customerId}  |  PUT /api/customers/{customerId}"""

    def _get_customer(self, customer_id):
        try:
            return Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            raise CustomerNotFoundException(f'No customer found with ID: {customer_id}')

    def get(self, request, customer_id):
        customer = self._get_customer(customer_id)
        agg = (
            customer.orders
            .aggregate(
                totalOrders=Count('id'),
                totalAmountSpent=Sum('items__price_at_time_of_order'),
            )
        )
        return Response({
            'status': 'success',
            'data': {
                'customerId': customer.id,
                'name': customer.name,
                'email': customer.email,
                'city': customer.city,
                'joinDate': str(customer.join_date),
                'totalOrders': agg['totalOrders'] or 0,
                'totalAmountSpent': float(agg['totalAmountSpent'] or 0),
            },
        })

    def put(self, request, customer_id):
        customer = self._get_customer(customer_id)
        ser = CustomerUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        vd = ser.validated_data

        if 'email' in vd and vd['email'] != customer.email:
            if Customer.objects.filter(email=vd['email']).exists():
                raise DuplicateEmailException()

        for field, value in vd.items():
            setattr(customer, field, value)
        customer.save()

        return Response({
            'status': 'success',
            'message': 'Customer profile updated',
            'data': {'customerId': customer.id, 'city': customer.city},
        })


class CustomerOrderHistoryView(APIView):
    """GET /api/customers/{customerId}/orders"""

    def get(self, request, customer_id):
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            raise CustomerNotFoundException(f'No customer found with ID: {customer_id}')

        orders = Order.objects.prefetch_related('items__book__author').filter(customer=customer)
        orders_data = _serialize_orders(orders)

        return Response({
            'status': 'success',
            'customerId': customer.id,
            'customerName': customer.name,
            'totalOrders': len(orders_data),
            'data': orders_data,
        })


def _serialize_orders(orders):
    result = []
    for order in orders:
        items_data = [
            {
                'bookId': item.book.id,
                'title': item.book.title,
                'quantity': item.quantity_ordered,
                'price': float(item.price_at_time_of_order),
            }
            for item in order.items.all()
        ]
        result.append({
            'orderId': order.id,
            'orderDate': str(order.order_date),
            'orderTotal': float(sum(i['price'] * i['quantity'] for i in items_data)),
            'items': items_data,
        })
    return result
