from django.db import models


class Author(models.Model):
    author_name = models.CharField(max_length=255)
    bio = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'authors'
        ordering = ['author_name']

    def __str__(self):
        return self.author_name


class Genre(models.Model):
    genre_name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'genres'
        ordering = ['genre_name']

    def __str__(self):
        return self.genre_name


class Book(models.Model):
    title = models.CharField(max_length=500)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    author = models.ForeignKey(Author, on_delete=models.PROTECT, related_name='books')
    genre = models.ForeignKey(Genre, on_delete=models.PROTECT, related_name='books')

    class Meta:
        db_table = 'books'

    def __str__(self):
        return self.title

    @property
    def in_stock(self):
        return self.stock_quantity > 0


class Customer(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    city = models.CharField(max_length=100)
    join_date = models.DateField()

    class Meta:
        db_table = 'customers'

    def __str__(self):
        return self.name


class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='orders')
    order_date = models.DateField()

    class Meta:
        db_table = 'orders'
        ordering = ['-order_date']

    def __str__(self):
        return f"Order #{self.pk} - {self.customer.name}"

    @property
    def order_total(self):
        return sum(item.subtotal for item in self.items.all())


class OrderDetail(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    book = models.ForeignKey(Book, on_delete=models.PROTECT, related_name='order_details')
    quantity_ordered = models.PositiveIntegerField()
    price_at_time_of_order = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'order_details'

    @property
    def subtotal(self):
        return self.quantity_ordered * self.price_at_time_of_order
