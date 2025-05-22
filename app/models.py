from app import db
from flask_login import UserMixin
from datetime import datetime
from enum import Enum
import bcrypt

# Định nghĩa OrderStatus ở mức cao nhất
class OrderStatus(Enum):
    PENDING = 'Chờ xác nhận'
    CONFIRMED = 'Đã xác nhận'
    PICKUP_PENDING = 'Chờ lấy hàng'
    SHIPPING = 'Đang giao hàng'
    DELIVERED = 'Đã giao hàng'
    CANCELLED = 'Đã hủy'

# Bảng User - Người dùng
class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Mối quan hệ với các bảng khác
    cart_items = db.relationship('CartItem', backref='user', lazy=True, cascade='save-update, merge')
    addresses = db.relationship('Address', backref='user', lazy=True, cascade='save-update, merge')
    comments = db.relationship('Comment', backref='user', lazy=True, cascade='save-update, merge')
    reactions = db.relationship('Reaction', backref='user', lazy=True, cascade='save-update, merge')
    orders = db.relationship('Order', backref='user', lazy=True, cascade='save-update, merge')

    @property
    def is_admin(self):
        return self.role == 'admin'

    def set_password(self, password):
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password):
        if not self.password_hash or '$' not in self.password_hash:
            return False
        try:
            return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
        except ValueError:
            return False

    def __repr__(self):
        return f'<User {self.username}>'

# Bảng Order - Đơn hàng
class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default=OrderStatus.PENDING.value)
    shipping_address = db.Column(db.Text, nullable=False)
    payment_method = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Thêm các trường mới cho theo dõi vận chuyển
    confirmed_at = db.Column(db.DateTime)
    pickup_at = db.Column(db.DateTime)
    shipping_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    estimated_delivery = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)
    shipping_notes = db.Column(db.Text)

    # Mối quan hệ với các bảng khác
    order_items = db.relationship('OrderItem', backref='order', lazy=True, cascade='save-update, merge')

    def __repr__(self):
        return f'<Order {self.id}>'

# Bảng Category - Danh mục sản phẩm
class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Mối quan hệ với các bảng khác
    products = db.relationship('Product', backref='category', lazy=True, cascade='save-update, merge')

    def __repr__(self):
        return f'<Category {self.name}>'

# Bảng Product - Sản phẩm
class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    discounted_price = db.Column(db.Float, nullable=True)
    image = db.Column(db.String(255), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    manufacturer = db.Column(db.String(100), nullable=False)
    stock = db.Column(db.Integer, default=0)
    featured = db.Column(db.Boolean, default=False)
    is_new = db.Column(db.Boolean, default=False)
    is_sale = db.Column(db.Boolean, default=False)
    rating = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Mối quan hệ với các bảng khác
    order_items = db.relationship('OrderItem', backref='product', lazy=True, cascade='save-update, merge')
    cart_items = db.relationship('CartItem', backref='product', lazy=True, cascade='save-update, merge')
    comments = db.relationship('Comment', backref='product', lazy=True, cascade='save-update, merge')

    def __repr__(self):
        return f'<Product {self.name}>'

# Bảng OrderItem - Chi tiết đơn hàng
class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<OrderItem {self.id}>'

# Bảng CartItem - Giỏ hàng
class CartItem(db.Model):
    __tablename__ = 'cart_items'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<CartItem {self.id}>'

# Bảng Address - Địa chỉ giao hàng
class Address(db.Model):
    __tablename__ = 'addresses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Address {self.id}>'

# Bảng Comment - Bình luận
class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    score = db.Column(db.Integer, nullable=True)
    criteria = db.Column(db.JSON, nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    reactions = db.relationship('Reaction', backref='comment', lazy=True, cascade='save-update, merge')
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy=True, cascade='save-update, merge')

    def __repr__(self):
        return f'<Comment {self.id}>'

# Bảng Reaction - Phản hồi (icon)
class Reaction(db.Model):
    __tablename__ = 'reactions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=False)
    emoji = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Reaction {self.id}>'