from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user, login_required
from app.models import Product, CartItem, Order, OrderItem
from app import db

cart = Blueprint('cart', __name__)

@cart.route('/cart')
@login_required
def view_cart():
    # Lấy tất cả các mục trong giỏ hàng của người dùng
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()

    # Tính tổng giá trị giỏ hàng
    total = 0
    for item in cart_items:
        if item.product.discounted_price:
            total += item.product.discounted_price * item.quantity
        else:
            total += item.product.price * item.quantity

    return render_template('cart/cart.html',
                           title='Giỏ hàng',
                           cart_items=cart_items,
                           total=total)

@cart.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)

    # Lấy số lượng từ form, mặc định là 1
    quantity = int(request.form.get('quantity', 1))

    # Kiểm tra xem sản phẩm đã có trong giỏ hàng chưa
    cart_item = CartItem.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()

    if cart_item:
        # Nếu đã có, tăng số lượng
        cart_item.quantity += quantity
    else:
        # Nếu chưa có, tạo mới
        cart_item = CartItem(
            user_id=current_user.id,
            product_id=product_id,
            quantity=quantity
        )
        db.session.add(cart_item)

    db.session.commit()
    flash(f'Đã thêm {product.name} vào giỏ hàng.', 'success')

    # Lấy trang trước đó hoặc trang chi tiết sản phẩm
    next_page = request.args.get('next') or url_for('products.product_detail', product_id=product_id)
    return redirect(next_page)

@cart.route('/cart/buy-now/<int:product_id>', methods=['GET'])
@login_required
def buy_now(product_id):
    product = Product.query.get_or_404(product_id)

    # Xóa tất cả các mục hiện có trong giỏ hàng
    CartItem.query.filter_by(user_id=current_user.id).delete()

    # Thêm sản phẩm mới vào giỏ hàng
    cart_item = CartItem(
        user_id=current_user.id,
        product_id=product_id,
        quantity=1  # Mặc định mua 1 sản phẩm
    )
    db.session.add(cart_item)
    db.session.commit()

    flash(f'Đã chọn {product.name} để mua ngay.', 'success')

    # Chuyển hướng đến trang thanh toán
    return redirect(url_for('cart.checkout'))

@cart.route('/cart/update/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)

    # Kiểm tra xem mục giỏ hàng có thuộc về người dùng hiện tại không
    if cart_item.user_id != current_user.id:
        flash('Bạn không có quyền truy cập vào mục này.', 'danger')
        return redirect(url_for('cart.view_cart'))

    # Cập nhật số lượng
    quantity = int(request.form.get('quantity', 1))
    if quantity < 1:
        quantity = 1

    cart_item.quantity = quantity
    db.session.commit()

    flash('Giỏ hàng đã được cập nhật.', 'success')
    return redirect(url_for('cart.view_cart'))

@cart.route('/cart/remove/<int:item_id>')
@login_required
def remove_from_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)

    # Kiểm tra xem mục giỏ hàng có thuộc về người dùng hiện tại không
    if cart_item.user_id != current_user.id:
        flash('Bạn không có quyền truy cập vào mục này.', 'danger')
        return redirect(url_for('cart.view_cart'))

    db.session.delete(cart_item)
    db.session.commit()

    flash('Sản phẩm đã được xóa khỏi giỏ hàng.', 'success')
    return redirect(url_for('cart.view_cart'))

@cart.route('/cart/clear')
@login_required
def clear_cart():
    # Xóa tất cả các mục trong giỏ hàng của người dùng
    CartItem.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()

    flash('Giỏ hàng đã được xóa.', 'success')
    return redirect(url_for('cart.view_cart'))

@cart.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    # Lấy tất cả các mục trong giỏ hàng của người dùng
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()

    # Nếu giỏ hàng trống, chuyển hướng về trang giỏ hàng
    if not cart_items:
        flash('Giỏ hàng của bạn đang trống.', 'warning')
        return redirect(url_for('cart.view_cart'))

    # Tính tổng giá trị đơn hàng
    total = 0
    for item in cart_items:
        if item.product.discounted_price:
            total += item.product.discounted_price * item.quantity
        else:
            total += item.product.price * item.quantity

    if request.method == 'POST':
        shipping_address = request.form.get('shipping_address')
        payment_method = request.form.get('payment_method')

        # Tạo đơn hàng mới
        order = Order(
            user_id=current_user.id,
            total_amount=total,
            shipping_address=shipping_address,
            payment_method=payment_method,
            status='pending'
        )
        db.session.add(order)
        db.session.flush()  # Để lấy order.id

        # Thêm các mục trong giỏ hàng vào chi tiết đơn hàng
        for item in cart_items:
            price = item.product.discounted_price or item.product.price
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=price
            )
            db.session.add(order_item)

        # Xóa giỏ hàng sau khi đặt hàng
        CartItem.query.filter_by(user_id=current_user.id).delete()

        db.session.commit()

        flash('Đơn hàng của bạn đã được tạo thành công!', 'success')
        return redirect(url_for('cart.order_confirmation', order_id=order.id))

    return render_template('cart/checkout.html',
                           title='Thanh toán',
                           cart_items=cart_items,
                           total=total)

@cart.route('/order-confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)

    # Kiểm tra xem đơn hàng có thuộc về người dùng hiện tại không
    if order.user_id != current_user.id:
        flash('Bạn không có quyền truy cập vào đơn hàng này.', 'danger')
        return redirect(url_for('main.index'))

    order_items = OrderItem.query.filter_by(order_id=order.id).all()

    return render_template('cart/order_confirmation.html',
                           title='Xác nhận đơn hàng',
                           order=order,
                           order_items=order_items)

@cart.route('/orders')
@login_required
def order_history():
    page = request.args.get('page', 1, type=int)
    orders = Order.query.filter_by(user_id=current_user.id).order_by(
        Order.created_at.desc()
    ).paginate(page=page, per_page=10)

    return render_template('cart/order_history.html',
                           title='Lịch sử đơn hàng',
                           orders=orders)

@cart.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)

    # Kiểm tra xem đơn hàng có thuộc về người dùng hiện tại không
    if order.user_id != current_user.id:
        flash('Bạn không có quyền truy cập vào đơn hàng này.', 'danger')
        return redirect(url_for('cart.order_history'))

    order_items = OrderItem.query.filter_by(order_id=order.id).all()

    return render_template('cart/order_detail.html',
                           title=f'Đơn hàng #{order.id}',
                           order=order,
                           order_items=order_items)