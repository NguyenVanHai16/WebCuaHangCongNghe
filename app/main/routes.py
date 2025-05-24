from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import current_user
from app.models import Product, Category
from app import db
from sqlalchemy import or_

main = Blueprint('main', __name__)

@main.route('/')
def index():
    # Lấy sản phẩm mới (chỉ lấy sản phẩm có is_new=True)
    new_products = Product.query.filter(
        Product.is_new == True
    ).order_by(Product.created_at.desc()).limit(4).all()

    # Lấy sản phẩm nổi bật (sản phẩm có is_hot, is_bestseller, hoặc is_limited)
    featured_products = Product.query.filter(
        or_(
            Product.is_hot == True,
            Product.is_bestseller == True,
            Product.is_limited == True
        )
    ).order_by(Product.rating.desc()).limit(4).all()

    # Lấy sản phẩm giảm giá (sản phẩm có is_sale=True hoặc discounted_price < price)
    sale_products = Product.query.filter(
        or_(
            Product.is_sale == True,
            (Product.discounted_price != None) & (Product.price > Product.discounted_price)
        )
    ).limit(4).all()

    return render_template('main/index.html',
                           title='TechMart - Cửa hàng công nghệ',
                           featured_products=featured_products,
                           new_products=new_products,
                           sale_products=sale_products)

# Các route khác giữ nguyên
@main.route('/about')
def about():
    return render_template('main/about.html', title='Về chúng tôi')

@main.route('/contact')
def contact():
    return render_template('main/contact.html', title='Liên hệ')

@main.route('/terms')
def terms():
    return render_template('main/terms.html', title='Điều khoản sử dụng')

@main.route('/privacy')
def privacy():
    return render_template('main/privacy.html', title='Chính sách bảo mật')

@main.route('/guide')
def guide():
    return render_template('main/guide.html', title='Hướng dẫn mua hàng')

@main.route('/payment')
def payment():
    return render_template('main/payment.html', title='Phương thức thanh toán')

@main.route('/shipping')
def shipping():
    return render_template('main/shipping.html', title='Chính sách vận chuyển')

@main.route('/warranty')
def warranty():
    return render_template('main/warranty.html', title='Chính sách bảo hành')