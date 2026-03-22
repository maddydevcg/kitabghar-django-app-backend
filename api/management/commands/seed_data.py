"""
Management command to seed the database with sample data from the API spec.
Usage: python manage.py seed_data
"""
import os
import django

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Seed the database with sample Kitab Ghar data'

    def handle(self, *args, **options):
        from api.models import Author, Genre, Book, Customer, Order, OrderDetail

        self.stdout.write('Seeding database...')

        # Authors
        a1 = Author.objects.get_or_create(id=1, defaults={'author_name': 'Chetan Bhagat', 'bio': 'Indian author known for 5 Point Someone.'})[0]
        a2 = Author.objects.get_or_create(id=2, defaults={'author_name': 'Arundhati Roy', 'bio': 'Indian author and activist.'})[0]
        a3 = Author.objects.get_or_create(id=3, defaults={'author_name': 'R.K. Narayan', 'bio': 'Indian writer known for Malgudi Days.'})[0]
        a4 = Author.objects.get_or_create(id=4, defaults={'author_name': 'Amish Tripathi', 'bio': 'Indian author of mythological fiction.'})[0]

        # Genres
        g1 = Genre.objects.get_or_create(id=1, defaults={'genre_name': 'Fiction'})[0]
        g2 = Genre.objects.get_or_create(id=2, defaults={'genre_name': 'Mythology'})[0]
        g3 = Genre.objects.get_or_create(id=3, defaults={'genre_name': 'History'})[0]
        g4 = Genre.objects.get_or_create(id=4, defaults={'genre_name': 'Romance'})[0]

        # Books
        b1 = Book.objects.get_or_create(id=1, defaults={'title': 'Five Point Someone', 'price': 250.00, 'stock_quantity': 50, 'author': a1, 'genre': g1})[0]
        b2 = Book.objects.get_or_create(id=2, defaults={'title': '2 States', 'price': 300.00, 'stock_quantity': 40, 'author': a1, 'genre': g4})[0]
        b3 = Book.objects.get_or_create(id=3, defaults={'title': 'The God of Small Things', 'price': 450.00, 'stock_quantity': 20, 'author': a2, 'genre': g1})[0]
        b4 = Book.objects.get_or_create(id=4, defaults={'title': 'Malgudi Days', 'price': 200.00, 'stock_quantity': 100, 'author': a3, 'genre': g1})[0]
        b5 = Book.objects.get_or_create(id=5, defaults={'title': 'The Immortals of Meluha', 'price': 399.00, 'stock_quantity': 60, 'author': a4, 'genre': g2})[0]

        # Customers
        c1 = Customer.objects.get_or_create(id=1, defaults={'name': 'Aarav Sharma', 'email': 'aarav@gmail.com', 'city': 'Mumbai', 'join_date': '2023-01-10'})[0]
        c2 = Customer.objects.get_or_create(id=2, defaults={'name': 'Diya Patel', 'email': 'diya.p@yahoo.com', 'city': 'Delhi', 'join_date': '2023-02-20'})[0]
        c3 = Customer.objects.get_or_create(id=3, defaults={'name': 'Vihaan Reddy', 'email': 'vihaan.r@gmail.com', 'city': 'Hyderabad', 'join_date': '2023-03-15'})[0]
        c4 = Customer.objects.get_or_create(id=4, defaults={'name': 'Ananya Gupta', 'email': 'ananya.g@gmail.com', 'city': 'Chennai', 'join_date': '2023-04-05'})[0]

        # Orders
        if not Order.objects.filter(id=1).exists():
            o1 = Order.objects.create(id=1, customer=c1, order_date='2023-05-01')
            OrderDetail.objects.create(order=o1, book=b1, quantity_ordered=1, price_at_time_of_order=250.00)
            OrderDetail.objects.create(order=o1, book=b4, quantity_ordered=2, price_at_time_of_order=200.00)
            b1.stock_quantity -= 1; b1.save()
            b4.stock_quantity -= 2; b4.save()

        if not Order.objects.filter(id=2).exists():
            o2 = Order.objects.create(id=2, customer=c2, order_date='2023-05-03')
            OrderDetail.objects.create(order=o2, book=b5, quantity_ordered=1, price_at_time_of_order=399.00)
            b5.stock_quantity -= 1; b5.save()

        if not Order.objects.filter(id=3).exists():
            o3 = Order.objects.create(id=3, customer=c1, order_date='2023-05-05')
            OrderDetail.objects.create(order=o3, book=b2, quantity_ordered=1, price_at_time_of_order=300.00)
            b2.stock_quantity -= 1; b2.save()

        if not Order.objects.filter(id=4).exists():
            o4 = Order.objects.create(id=4, customer=c3, order_date='2023-06-10')
            OrderDetail.objects.create(order=o4, book=b3, quantity_ordered=1, price_at_time_of_order=450.00)
            b3.stock_quantity -= 1; b3.save()

        self.stdout.write(self.style.SUCCESS('✅ Database seeded successfully!'))
        self.stdout.write('  • 4 authors, 4 genres, 5 books')
        self.stdout.write('  • 4 customers, 4 orders')
