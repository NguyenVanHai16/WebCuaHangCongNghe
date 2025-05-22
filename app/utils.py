import os
from datetime import datetime
from app.models import User, Category, Product, Order
from functools import wraps
from flask import redirect, url_for
from flask_login import current_user

def get_current_time():
    """Trả về thời gian hiện tại"""
    return datetime.utcnow()

def format_currency(amount):
    """Định dạng số tiền theo định dạng tiền tệ Việt Nam"""
    if amount is None:
        return "0 ₫"
    return f"{amount:,.0f} ₫"

def calculate_discount_percentage(original_price, discounted_price):
    """Tính tỷ lệ phần trăm giảm giá"""
    if not original_price or not discounted_price or original_price <= 0:
        return 0
    discount = ((original_price - discounted_price) / original_price) * 100
    return round(discount)

def get_cart_count(user):
    """Lấy số lượng mặt hàng trong giỏ của người dùng"""
    if not user or not user.is_authenticated:
        return 0
    return sum(item.quantity for item in user.cart_items)

def get_cart_total(user):
    """Tính tổng giá trị giỏ hàng của người dùng"""
    if not user or not user.is_authenticated:
        return 0

    total = 0
    for item in user.cart_items:
        if item.product.discounted_price:
            total += item.product.discounted_price * item.quantity
        else:
            total += item.product.price * item.quantity

    return total

def get_order_status_label(status):
    """Lấy nhãn trạng thái đơn hàng đã được địa phương hóa"""
    status_map = {
        'pending': 'Chờ xử lý',
        'processing': 'Đang xử lý',
        'shipped': 'Đã giao hàng',
        'delivered': 'Đã nhận hàng',
        'cancelled': 'Đã hủy'
    }
    return status_map.get(status, status)

def create_admin_user(username, email, password):
    """Tạo người dùng quản trị viên mới nếu không có"""
    if not User.query.filter_by(role='admin').first():
        admin = User(
            username=username,
            email=email,
            role='admin'
        )
        admin.set_password(password)
        return admin
    return None

def admin_required(f):
    """Decorator để yêu cầu quyền admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def seed_initial_data():
    """
    Tạo dữ liệu ban đầu cho cửa hàng nếu cơ sở dữ liệu trống.
    Bao gồm danh mục và một số sản phẩm mẫu.
    """
    # Kiểm tra xem đã có dữ liệu chưa
    if Category.query.first() is not None:
        return False

    # Tạo danh mục
    categories = [
        {
            'name': 'Laptop',
            'slug': 'laptops',
            'description': 'Các sản phẩm laptop từ nhiều thương hiệu',
            'image_url': 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853'
        },
        {
            'name': 'Điện thoại',
            'slug': 'smartphones',
            'description': 'Điện thoại thông minh và phụ kiện',
            'image_url': 'https://images.unsplash.com/photo-1598327105666-5b89351aff97'
        },
        {
            'name': 'Máy tính bảng',
            'slug': 'tablets',
            'description': 'Các loại máy tính bảng',
            'image_url': 'https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0'
        },
        {
            'name': 'Phụ kiện',
            'slug': 'accessories',
            'description': 'Phụ kiện công nghệ',
            'image_url': 'https://images.unsplash.com/photo-1588872657578-7efd1f1555ed'
        }
    ]

    category_objects = []
    for cat_data in categories:
        category = Category(**cat_data)
        category_objects.append(category)

    # Tạo một số sản phẩm mẫu
    products = [
        {
            'name': 'MacBook Pro 13"',
            'description': 'Laptop Apple MacBook Pro 13 inch với chip M1, RAM 8GB, SSD 256GB',
            'price': 30990000,
            'discounted_price': 29490000,
            'image_url': 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8',
            'manufacturer': 'Apple',
            'stock': 10,
            'featured': True,
            'is_new': True,
            'is_sale': True,
            'rating': 4.8,
            'category_id': 1
        },
        {
            'name': 'iPhone 13 Pro',
            'description': 'iPhone 13 Pro với màn hình Super Retina XDR 6.1 inch, chip A15 Bionic, bộ nhớ 128GB',
            'price': 25990000,
            'discounted_price': None,
            'image_url': 'https://images.unsplash.com/photo-1632661674596-df8be070a5c5',
            'manufacturer': 'Apple',
            'stock': 15,
            'featured': True,
            'is_new': True,
            'is_sale': False,
            'rating': 4.9,
            'category_id': 2
        },
        {
            'name': 'Samsung Galaxy S21',
            'description': 'Samsung Galaxy S21 với màn hình Dynamic AMOLED 2X 6.2 inch, chip Exynos 2100, RAM 8GB, bộ nhớ 128GB',
            'price': 20990000,
            'discounted_price': 18990000,
            'image_url': 'https://images.unsplash.com/photo-1610945415295-d9bbf067e59c',
            'manufacturer': 'Samsung',
            'stock': 12,
            'featured': True,
            'is_new': False,
            'is_sale': True,
            'rating': 4.7,
            'category_id': 2
        },
        {
            'name': 'iPad Pro 11"',
            'description': 'iPad Pro 11 inch với chip M1, bộ nhớ 128GB, WiFi',
            'price': 19990000,
            'discounted_price': None,
            'image_url': 'https://images.unsplash.com/photo-1557825835-70d97c4aa567',
            'manufacturer': 'Apple',
            'stock': 8,
            'featured': False,
            'is_new': True,
            'is_sale': False,
            'rating': 4.8,
            'category_id': 3
        },
        {
            'name': 'AirPods Pro',
            'description': 'Tai nghe không dây Apple AirPods Pro với công nghệ khử tiếng ồn chủ động',
            'price': 5990000,
            'discounted_price': 5490000,
            'image_url': 'https://images.unsplash.com/photo-1588423771073-b8903fbb85b5',
            'manufacturer': 'Apple',
            'stock': 20,
            'featured': True,
            'is_new': False,
            'is_sale': True,
            'rating': 4.6,
            'category_id': 4
        },
        {
            'name': 'Asus ROG Zephyrus G14',
            'description': 'Laptop gaming Asus ROG Zephyrus G14 với CPU AMD Ryzen 9, GPU NVIDIA GeForce RTX 3060, RAM 16GB, SSD 1TB',
            'price': 35990000,
            'discounted_price': None,
            'image_url': 'https://images.unsplash.com/photo-1593642702821-c8da6771f0c6',
            'manufacturer': 'Asus',
            'stock': 5,
            'featured': False,
            'is_new': True,
            'is_sale': False,
            'rating': 4.7,
            'category_id': 1
        }
    ]

    product_objects = []
    for prod_data in products:
        product = Product(**prod_data)
        product_objects.append(product)

    return category_objects, product_objects