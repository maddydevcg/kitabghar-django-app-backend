from datetime import date, timedelta

from django.db.models import Sum, Count, Q

from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Author, Customer, Genre, Order, OrderDetail


class RevenueView(APIView):
    """GET /api/reports/revenue?from=&to="""

    def get(self, request):
        from_date = request.query_params.get('from')
        to_date = request.query_params.get('to')

        qs = OrderDetail.objects.select_related('order')
        if from_date:
            qs = qs.filter(order__order_date__gte=from_date)
        if to_date:
            qs = qs.filter(order__order_date__lte=to_date)

        agg = qs.aggregate(
            total=Sum('price_at_time_of_order'),
            orders=Count('order', distinct=True),
        )
        total = float(agg['total'] or 0)
        orders = agg['orders'] or 0
        avg = round(total / orders, 2) if orders else 0

        return Response({
            'status': 'success',
            'period': {'from': from_date, 'to': to_date},
            'totalOrders': orders,
            'totalRevenue': total,
            'averageOrderValue': avg,
        })


class RevenueByGenreView(APIView):
    """GET /api/reports/revenue-by-genre"""

    def get(self, request):
        genres = Genre.objects.all()
        data = []
        for genre in genres:
            agg = OrderDetail.objects.filter(book__genre=genre).aggregate(
                totalRevenue=Sum('price_at_time_of_order'),
                booksSold=Sum('quantity_ordered'),
            )
            data.append({
                'genreId': genre.id,
                'genreName': genre.genre_name,
                'totalRevenue': float(agg['totalRevenue'] or 0),
                'booksSold': agg['booksSold'] or 0,
            })
        data.sort(key=lambda x: x['totalRevenue'], reverse=True)
        return Response({'status': 'success', 'data': data})


class RevenueByAuthorView(APIView):
    """GET /api/reports/revenue-by-author"""

    def get(self, request):
        authors = Author.objects.all()
        data = []
        for author in authors:
            agg = OrderDetail.objects.filter(book__author=author).aggregate(
                totalRevenue=Sum('price_at_time_of_order'),
                totalUnitsSold=Sum('quantity_ordered'),
            )
            data.append({
                'authorId': author.id,
                'authorName': author.author_name,
                'totalRevenue': float(agg['totalRevenue'] or 0),
                'totalUnitsSold': agg['totalUnitsSold'] or 0,
            })
        data.sort(key=lambda x: x['totalRevenue'], reverse=True)
        return Response({'status': 'success', 'data': data})


class ReportsBestsellersView(APIView):
    """GET /api/reports/bestsellers?limit=5&from=&to="""

    def get(self, request):
        limit = int(request.query_params.get('limit', 5))
        from_date = request.query_params.get('from')
        to_date = request.query_params.get('to')

        qs = OrderDetail.objects.select_related('book__author', 'book__genre')
        if from_date:
            qs = qs.filter(order__order_date__gte=from_date)
        if to_date:
            qs = qs.filter(order__order_date__lte=to_date)

        results = (
            qs.values(
                'book__id', 'book__title',
                'book__author__author_name', 'book__genre__genre_name',
            )
            .annotate(
                totalQuantitySold=Sum('quantity_ordered'),
                totalRevenue=Sum('price_at_time_of_order'),
            )
            .order_by('-totalQuantitySold')[:limit]
        )

        data = [
            {
                'bookId': r['book__id'],
                'title': r['book__title'],
                'author': r['book__author__author_name'],
                'genre': r['book__genre__genre_name'],
                'totalQuantitySold': r['totalQuantitySold'],
                'totalRevenue': float(r['totalRevenue'] or 0),
            }
            for r in results
        ]
        return Response({'status': 'success', 'data': data})


class CustomerWithMostOrdersView(APIView):
    """GET /api/reports/customer-with-most-orders"""

    def get(self, request):
        customer = (
            Customer.objects
            .annotate(
                totalOrders=Count('orders'),
                totalAmountSpent=Sum('orders__items__price_at_time_of_order'),
            )
            .order_by('-totalOrders')
            .first()
        )
        if not customer:
            return Response({'status': 'success', 'data': None})

        return Response({
            'status': 'success',
            'data': {
                'customerId': customer.id,
                'name': customer.name,
                'email': customer.email,
                'city': customer.city,
                'totalOrders': customer.totalOrders,
                'totalAmountSpent': float(customer.totalAmountSpent or 0),
            },
        })


class InactiveCustomersView(APIView):
    """GET /api/reports/inactive-customers?months=6"""

    def get(self, request):
        months = int(request.query_params.get('months', 6))
        cutoff = date.today() - timedelta(days=months * 30)

        # Customers whose most recent order is before cutoff, OR have no orders at all
        active_customer_ids = (
            Order.objects
            .filter(order_date__gte=cutoff)
            .values_list('customer_id', flat=True)
            .distinct()
        )

        from django.db.models import Max
        inactive = (
            Customer.objects
            .exclude(id__in=active_customer_ids)
            .annotate(lastOrderDate=Max('orders__order_date'))
        )

        data = [
            {
                'customerId': c.id,
                'name': c.name,
                'email': c.email,
                'lastOrderDate': str(c.lastOrderDate) if c.lastOrderDate else None,
            }
            for c in inactive
        ]

        return Response({
            'status': 'success',
            'inactiveSince': str(cutoff),
            'count': len(data),
            'data': data,
        })
