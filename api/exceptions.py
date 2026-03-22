from datetime import datetime
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


class KitabGharAPIException(Exception):
    """Base class for domain-level errors."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'API_ERROR'
    default_message = 'An error occurred.'

    def __init__(self, message=None, code=None):
        self.message = message or self.default_message
        self.code = code or self.default_code


class BookNotFoundException(KitabGharAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_code = 'BOOK_NOT_FOUND'
    default_message = 'Book not found.'


class AuthorNotFoundException(KitabGharAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_code = 'AUTHOR_NOT_FOUND'
    default_message = 'Author not found.'


class CustomerNotFoundException(KitabGharAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_code = 'CUSTOMER_NOT_FOUND'
    default_message = 'Customer not found.'


class OrderNotFoundException(KitabGharAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_code = 'ORDER_NOT_FOUND'
    default_message = 'Order not found.'


class GenreNotFoundException(KitabGharAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_code = 'GENRE_NOT_FOUND'
    default_message = 'Genre not found.'


class InsufficientStockException(KitabGharAPIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = 'INSUFFICIENT_STOCK'


class AuthorHasBooksException(KitabGharAPIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = 'AUTHOR_HAS_BOOKS'
    default_message = 'Cannot delete author with existing books. Remove books first.'


class GenreHasBooksException(KitabGharAPIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = 'GENRE_HAS_BOOKS'
    default_message = 'Cannot delete genre with existing books.'


class DuplicateEmailException(KitabGharAPIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = 'DUPLICATE_EMAIL'
    default_message = 'Customer email already registered.'


def error_response(code, message, http_status, errors=None):
    payload = {
        'status': 'error',
        'code': code,
        'message': message,
        'timestamp': datetime.now().isoformat(),
    }
    if errors:
        payload['errors'] = errors
    return Response(payload, status=http_status)


def custom_exception_handler(exc, context):
    if isinstance(exc, KitabGharAPIException):
        return error_response(exc.code, exc.message, exc.status_code)

    # Delegate to DRF default for validation errors etc.
    response = exception_handler(exc, context)

    if response is not None:
        errors = None
        if isinstance(response.data, dict):
            errors = [
                {'field': field, 'issue': str(msgs[0]) if isinstance(msgs, list) else str(msgs)}
                for field, msgs in response.data.items()
                if field not in ('detail',)
            ]
        detail = response.data.get('detail', str(exc)) if isinstance(response.data, dict) else str(exc)
        return error_response(
            'VALIDATION_ERROR' if response.status_code == 400 else 'INTERNAL_SERVER_ERROR',
            str(detail),
            response.status_code,
            errors or None,
        )

    return error_response('INTERNAL_SERVER_ERROR', str(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
