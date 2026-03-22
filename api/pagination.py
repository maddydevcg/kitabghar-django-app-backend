from django.core.paginator import Paginator


def paginate_queryset(queryset, request):
    """
    Returns (page_data, meta_dict) using standard page/size/sort/order params.
    """
    page = int(request.query_params.get('page', 0))
    size = int(request.query_params.get('size', 10))
    sort = request.query_params.get('sort', None)
    order = request.query_params.get('order', 'asc')

    if sort:
        prefix = '' if order == 'asc' else '-'
        # Map camelCase param to model field if needed
        field_map = {
            'price': 'price',
            'title': 'title',
            'authorName': 'author_name',
            'orderDate': 'order_date',
            'name': 'name',
        }
        sort_field = field_map.get(sort, sort)
        queryset = queryset.order_by(f'{prefix}{sort_field}')

    paginator = Paginator(queryset, size)
    # page is 0-based per spec
    page_obj = paginator.page(page + 1) if page + 1 <= paginator.num_pages else paginator.page(1)

    meta = {
        'page': page,
        'size': size,
        'totalElements': paginator.count,
        'totalPages': paginator.num_pages,
    }
    return list(page_obj.object_list), meta
