from rest_framework import serializers
from .models import Author, Genre, Book, Customer, Order, OrderDetail


# ── Author ────────────────────────────────────────────────────────────────────

class AuthorBriefSerializer(serializers.ModelSerializer):
    authorId = serializers.IntegerField(source='id', read_only=True)
    authorName = serializers.CharField(source='author_name')

    class Meta:
        model = Author
        fields = ['authorId', 'authorName']


class AuthorDetailSerializer(serializers.ModelSerializer):
    authorId = serializers.IntegerField(source='id', read_only=True)
    authorName = serializers.CharField(source='author_name')
    bio = serializers.CharField()

    class Meta:
        model = Author
        fields = ['authorId', 'authorName', 'bio']


class AuthorWriteSerializer(serializers.ModelSerializer):
    authorName = serializers.CharField(source='author_name')
    bio = serializers.CharField(required=False, default='')

    class Meta:
        model = Author
        fields = ['authorName', 'bio']


# ── Genre ────────────────────────────────────────────────────────────────────

class GenreBriefSerializer(serializers.ModelSerializer):
    genreId = serializers.IntegerField(source='id', read_only=True)
    genreName = serializers.CharField(source='genre_name')

    class Meta:
        model = Genre
        fields = ['genreId', 'genreName']


class GenreWriteSerializer(serializers.ModelSerializer):
    genreName = serializers.CharField(source='genre_name')

    class Meta:
        model = Genre
        fields = ['genreName']


# ── Book ─────────────────────────────────────────────────────────────────────

class BookListSerializer(serializers.ModelSerializer):
    bookId = serializers.IntegerField(source='id', read_only=True)
    stockQuantity = serializers.IntegerField(source='stock_quantity')
    inStock = serializers.SerializerMethodField()
    author = AuthorBriefSerializer(read_only=True)
    genre = GenreBriefSerializer(read_only=True)

    class Meta:
        model = Book
        fields = ['bookId', 'title', 'price', 'stockQuantity', 'author', 'genre', 'inStock']

    def get_inStock(self, obj):
        return obj.in_stock


class BookDetailSerializer(BookListSerializer):
    author = serializers.SerializerMethodField()

    def get_author(self, obj):
        return {
            'authorId': obj.author.id,
            'authorName': obj.author.author_name,
            'bio': obj.author.bio,
        }

    class Meta(BookListSerializer.Meta):
        fields = ['bookId', 'title', 'price', 'stockQuantity', 'inStock', 'author', 'genre']


class BookWriteSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=500)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    stockQuantity = serializers.IntegerField(source='stock_quantity', min_value=0)
    authorId = serializers.IntegerField()
    genreId = serializers.IntegerField()

    def validate_authorId(self, value):
        from .exceptions import AuthorNotFoundException
        from .models import Author
        if not Author.objects.filter(pk=value).exists():
            raise AuthorNotFoundException(f'No author found with ID: {value}')
        return value

    def validate_genreId(self, value):
        from .exceptions import GenreNotFoundException
        from .models import Genre
        if not Genre.objects.filter(pk=value).exists():
            raise GenreNotFoundException(f'No genre found with ID: {value}')
        return value


# ── Customer ─────────────────────────────────────────────────────────────────

class CustomerWriteSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    city = serializers.CharField(max_length=100)
    joinDate = serializers.DateField(source='join_date')

    class Meta:
        model = Customer
        fields = ['name', 'email', 'city', 'joinDate']


class CustomerUpdateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=255, required=False)
    email = serializers.EmailField(required=False)
    city = serializers.CharField(max_length=100, required=False)

    class Meta:
        model = Customer
        fields = ['name', 'email', 'city']


# ── Order ────────────────────────────────────────────────────────────────────

class OrderItemWriteSerializer(serializers.Serializer):
    bookId = serializers.IntegerField()
    quantityOrdered = serializers.IntegerField(min_value=1)


class OrderWriteSerializer(serializers.Serializer):
    customerId = serializers.IntegerField()
    orderDate = serializers.DateField()
    items = OrderItemWriteSerializer(many=True, min_length=1)


class OrderDetailLineSerializer(serializers.ModelSerializer):
    detailId = serializers.IntegerField(source='id', read_only=True)
    book = serializers.SerializerMethodField()
    quantityOrdered = serializers.IntegerField(source='quantity_ordered')
    priceAtTimeOfOrder = serializers.DecimalField(source='price_at_time_of_order', max_digits=10, decimal_places=2)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderDetail
        fields = ['detailId', 'book', 'quantityOrdered', 'priceAtTimeOfOrder', 'subtotal']

    def get_book(self, obj):
        return {
            'bookId': obj.book.id,
            'title': obj.book.title,
            'author': obj.book.author.author_name,
        }


# ── Inventory ─────────────────────────────────────────────────────────────────

class RestockSerializer(serializers.Serializer):
    additionalQuantity = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=500, required=False, default='')
