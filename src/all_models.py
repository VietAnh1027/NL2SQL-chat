# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class CartItems(models.Model):
    cart_item_id = models.AutoField(primary_key=True)
    cart = models.ForeignKey('ShoppingCart', models.DO_NOTHING, blank=True, null=True)
    product = models.ForeignKey('Products', models.DO_NOTHING, blank=True, null=True)
    quantity = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'cart_items'


class Categories(models.Model):
    category_id = models.AutoField(primary_key=True)
    category_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'categories'


class Customers(models.Model):
    user_id = models.AutoField(primary_key=True)
    full_name = models.CharField(max_length=100)
    email = models.CharField(unique=True, max_length=100)
    password_hash = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'customers'


class OrderItems(models.Model):
    order_item_id = models.AutoField(primary_key=True)
    order = models.ForeignKey('Orders', models.DO_NOTHING, blank=True, null=True)
    product = models.ForeignKey('Products', models.DO_NOTHING, blank=True, null=True)
    quantity = models.IntegerField()
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'order_items'


class Orders(models.Model):
    order_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(Customers, models.DO_NOTHING, blank=True, null=True)
    order_date = models.DateTimeField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'orders'


class Payments(models.Model):
    payment_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Orders, models.DO_NOTHING, blank=True, null=True)
    payment_method = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=50, blank=True, null=True)
    transaction_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'payments'


class Products(models.Model):
    product_id = models.AutoField(primary_key=True)
    product_name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField()
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Categories, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'products'


class Reviews(models.Model):
    review_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(Customers, models.DO_NOTHING, blank=True, null=True)
    product = models.ForeignKey(Products, models.DO_NOTHING, blank=True, null=True)
    rating = models.IntegerField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    review_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'reviews'


class Shipping(models.Model):
    shipping_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Orders, models.DO_NOTHING, blank=True, null=True)
    shipping_address = models.TextField()
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    shipped_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'shipping'


class ShoppingCart(models.Model):
    cart_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(Customers, models.DO_NOTHING, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'shopping_cart'
