from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from app.models import Product, CartItem, Order, OrderItem, Address
from app import db
import secrets
import logging

# Thiết lập logging
logging.basicConfig(level=logging.DEBUG)

cart = Blueprint('cart', __name__)

@cart.route('/cart')
@login_required
def view_cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = 0
    for item in cart_items:
        if item.product.discounted_price:
            total += item.product.discounted_price * item.quantity
        else:
            total += item.product.price * item.quantity
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)
    return render_template('cart/cart.html', title='Giỏ hàng', cart_items=cart_items, total=total)

@cart.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    logging.debug(f"Add to cart: product_id={product_id}, headers={request.headers}")
    logging.debug(f"Current user: {current_user.is_authenticated}, User ID: {current_user.id if current_user.is_authenticated else 'None'}")
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Vui lòng đăng nhập để thêm sản phẩm vào giỏ hàng.'}), 401
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get('quantity', 1))

    # Kiểm tra CSRF token
    form_csrf_token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
    session_csrf_token = session.get('csrf_token')
    logging.debug(f"Session CSRF token: {session_csrf_token}, Form/Header CSRF token: {form_csrf_token}")
    logging.debug(f"Request form: {request.form}")
    if not form_csrf_token or form_csrf_token != session_csrf_token:
        logging.debug("CSRF token validation failed")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.accept_mimetypes.accept_json:
            return jsonify({'success': False, 'message': 'Lỗi bảo mật: CSRF token không hợp lệ.'}), 403
        flash('Lỗi bảo mật: CSRF token không hợp lệ.', 'danger')
        return redirect(url_for('products.product_detail', product_id=product_id))

    if quantity <= 0 or quantity > product.stock:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.accept_mimetypes.accept_json:
            return jsonify({'success': False, 'message': 'Số lượng không hợp lệ hoặc vượt quá tồn kho!'}), 400
        flash('Số lượng không hợp lệ hoặc vượt quá tồn kho!', 'danger')
        return redirect(url_for('products.product_detail', product_id=product_id))

    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if cart_item:
        cart_item.quantity += quantity
        if cart_item.quantity > product.stock:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.accept_mimetypes.accept_json:
                return jsonify({'success': False, 'message': 'Số lượng vượt quá tồn kho!'}), 400
            flash('Số lượng vượt quá tồn kho!', 'danger')
            return redirect(url_for('cart.view_cart'))
    else:
        cart_item = CartItem(user_id=current_user.id, product_id=product_id, quantity=quantity)
        db.session.add(cart_item)

    try:
        db.session.commit()
        logging.debug(f"Successfully added product {product_id} to cart for user {current_user.id}")
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to commit cart item: {str(e)}")
        return jsonify({'success': False, 'message': 'Lỗi khi lưu vào giỏ hàng.'}), 500

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.accept_mimetypes.accept_json:
        return jsonify({
            'success': True,
            'message': f'Đã thêm {product.name} vào giỏ hàng.',
            'csrf_token': session.get('csrf_token')
        })
    flash(f'Đã thêm {product.name} vào giỏ hàng.', 'success')
    return redirect(url_for('cart.view_cart'))

@cart.route('/cart/buy-now/<int:product_id>', methods=['POST'])
@login_required
def buy_now(product_id):
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get('quantity', 1))
    form_csrf_token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
    session_csrf_token = session.get('csrf_token')

    if not form_csrf_token or form_csrf_token != session_csrf_token:
        logging.debug("CSRF token validation failed")
        return jsonify({'success': False, 'message': 'Lỗi bảo mật: CSRF token không hợp lệ.'}), 403

    if quantity <= 0 or quantity > product.stock:
        return jsonify({'success': False, 'message': 'Số lượng không hợp lệ hoặc vượt quá tồn kho!'}), 400

    # Xóa giỏ hàng hiện tại
    CartItem.query.filter_by(user_id=current_user.id).delete()
    cart_item = CartItem(user_id=current_user.id, product_id=product_id, quantity=quantity)
    db.session.add(cart_item)
    db.session.commit()

    # Lưu ID sản phẩm được chọn vào session
    session['selected_item_ids'] = [str(cart_item.id)]

    return jsonify({'success': True, 'message': f'Đã chọn {product.name} để mua ngay.'})

@cart.route('/cart/update/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    if cart_item.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Bạn không có quyền truy cập vào mục này.'}), 403
    quantity = int(request.form.get('quantity', 1))
    if quantity < 1:
        quantity = 1
    if quantity > cart_item.product.stock:
        return jsonify({'success': False, 'message': 'Số lượng vượt quá tồn kho!'}), 400
    cart_item.quantity = quantity
    db.session.commit()
    price = cart_item.product.discounted_price or cart_item.product.price
    subtotal = price * quantity
    return jsonify({
        'success': True,
        'message': 'Giỏ hàng đã được cập nhật.',
        'subtotal': subtotal,
        'quantity': quantity
    })

@cart.route('/cart/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    if cart_item.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Bạn không có quyền truy cập vào mục này.'}), 403
    db.session.delete(cart_item)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Sản phẩm đã được xóa khỏi giỏ hàng.'})

@cart.route('/cart/clear')
@login_required
def clear_cart():
    CartItem.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash('Giỏ hàng đã được xóa.', 'success')
    return redirect(url_for('cart.view_cart'))

@cart.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    logging.debug(f"Request method: {request.method}")
    logging.debug(f"Form data: {request.form}")
    logging.debug(f"Headers: {request.headers}")

    # Kiểm tra CSRF token
    if request.method == 'POST':
        form_csrf_token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
        session_csrf_token = session.get('csrf_token')
        logging.debug(f"Form/Header CSRF token: {form_csrf_token}, Session CSRF token: {session_csrf_token}")
        if not form_csrf_token or form_csrf_token != session_csrf_token:
            logging.debug("CSRF token validation failed")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': 'Lỗi bảo mật: CSRF token không hợp lệ.'}), 403
            flash('Lỗi bảo mật: CSRF token không hợp lệ.', 'danger')
            return redirect(url_for('cart.view_cart'))

        # Lưu danh sách selected_item_ids vào session
        selected_item_ids = request.form.getlist('selected_items[]')
        logging.debug(f"Selected item IDs from form: {selected_item_ids}")
        if not selected_item_ids:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': 'Vui lòng chọn ít nhất một sản phẩm để thanh toán.'}), 400
            flash('Vui lòng chọn ít nhất một sản phẩm để thanh toán.', 'warning')
            return redirect(url_for('cart.view_cart'))

        session['selected_item_ids'] = selected_item_ids

        # Nếu là AJAX request, trả về JSON để client chuyển hướng
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Danh sách sản phẩm đã được chọn để thanh toán.'})

        # Xử lý thanh toán (form submission không phải AJAX)
        shipping_address = request.form.get('shipping_address')
        payment_method = request.form.get('payment_method')
        customer_name = request.form.get('customer_name')
        phone_number = request.form.get('phone_number')

        if not all([shipping_address, payment_method, customer_name, phone_number]):
            logging.debug(f"Missing required fields: shipping_address={bool(shipping_address)}, "
                          f"payment_method={bool(payment_method)}, customer_name={bool(customer_name)}, "
                          f"phone_number={bool(phone_number)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': 'Vui lòng cung cấp đầy đủ thông tin thanh toán.'}), 400
            flash('Vui lòng cung cấp đầy đủ thông tin thanh toán.', 'danger')
            return redirect(url_for('cart.checkout'))

        # Lấy danh sách sản phẩm được chọn
        try:
            checkout_items = CartItem.query.filter(
                CartItem.user_id == current_user.id,
                CartItem.id.in_([int(id) for id in selected_item_ids])
            ).all()
            logging.debug(f"Checkout items: {[item.id for item in checkout_items]}")
        except ValueError as e:
            logging.error(f"Invalid item ID format: {e}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': 'Dữ liệu sản phẩm không hợp lệ.'}), 400
            flash('Dữ liệu sản phẩm không hợp lệ.', 'danger')
            return redirect(url_for('cart.view_cart'))

        if not checkout_items:
            logging.debug(f"No matching checkout items found for IDs: {selected_item_ids}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': 'Giỏ hàng của bạn trống hoặc sản phẩm không hợp lệ.'}), 404
            flash('Giỏ hàng của bạn đang trống hoặc các sản phẩm đã chọn không hợp lệ.', 'warning')
            return redirect(url_for('cart.view_cart'))

        # Tính tổng tiền
        total = 0
        for item in checkout_items:
            if item.product.discounted_price:
                total += item.product.discounted_price * item.quantity
            else:
                total += item.product.price * item.quantity
            logging.debug(f"Adding to total: {item.product.name} - {total} ₫")

        # Tạo đơn hàng
        full_shipping_address = f"Tên: {customer_name}, SĐT: {phone_number}, Địa chỉ: {shipping_address}"
        order = Order(
            user_id=current_user.id,
            total_amount=total,
            shipping_address=full_shipping_address,
            payment_method=payment_method,
            status='pending'
        )
        db.session.add(order)
        db.session.flush()

        for item in checkout_items:
            price = item.product.discounted_price or item.product.price
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=price
            )
            db.session.add(order_item)

        # Xóa toàn bộ giỏ hàng
        CartItem.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()

        session.pop('csrf_token', None)
        session.pop('selected_item_ids', None)
        flash('Đơn hàng của bạn đã được tạo thành công!', 'success')
        return redirect(url_for('cart.orders'))

    # GET request: Hiển thị trang checkout
    selected_item_ids = session.get('selected_item_ids', [])
    logging.debug(f"Selected item IDs from session (GET): {selected_item_ids}")

    if selected_item_ids:
        try:
            checkout_items = CartItem.query.filter(
                CartItem.user_id == current_user.id,
                CartItem.id.in_([int(id) for id in selected_item_ids])
            ).all()
            logging.debug(f"Checkout items for GET: {[item.id for item in checkout_items]}")
        except ValueError as e:
            logging.error(f"Invalid item ID format: {e}")
            flash('Dữ liệu sản phẩm không hợp lệ.', 'danger')
            return redirect(url_for('cart.view_cart'))
    else:
        checkout_items = []
        logging.debug("No selected items in session for GET request")

    if not checkout_items:
        flash('Giỏ hàng của bạn đang trống hoặc các sản phẩm không hợp lệ.', 'warning')
        return redirect(url_for('cart.view_cart'))

    total = 0
    for item in checkout_items:
        if item.product.discounted_price:
            total += item.product.discounted_price * item.quantity
        else:
            total += item.product.price * item.quantity
        logging.debug(f"Adding to total (GET): {item.product.name} - {total} ₫")

    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)
    csrf_token = session['csrf_token']
    logging.debug(f"CSRF token: {csrf_token}")

    return render_template('cart/checkout.html', title='Thanh toán', checkout_items=checkout_items, total=total,
                           csrf_token=csrf_token)

@cart.route('/order-confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('Bạn không có quyền truy cập vào đơn hàng này.', 'danger')
        return redirect(url_for('main.index'))
    order_items = OrderItem.query.filter_by(order_id=order.id).all()
    return render_template('cart/order_confirmation.html', title='Xác nhận đơn hàng', order=order,
                           order_items=order_items)

@cart.route('/orders')
@login_required
def orders():
    status_labels = {
        "pending": "Chờ xác nhận",
        "confirmed": "Đã xác nhận",
        "pickup_pending": "Chờ lấy hàng",
        "shipping": "Đang giao hàng",
        "delivered": "Đã giao hàng",
        "cancelled": "Đã hủy"
    }
    all_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    logging.debug(f"Orders found for user {current_user.id}: {[order.id for order in all_orders]}")

    def get_order_status_label(status):
        return status_labels.get(status, "Không xác định")

    return render_template('orders/my_orders.html', title='Đơn mua của tôi', orders=all_orders,
                           status_labels=status_labels, get_order_status_label=get_order_status_label)

@cart.route('/order_history')
@login_required
def order_history():
    page = request.args.get('page', 1, type=int)
    orders = Order.query.filter_by(user_id=current_user.id).filter(
        Order.status.in_(['delivered', 'cancelled'])).order_by(Order.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('cart/order_history.html', title='Lịch sử đơn hàng', orders=orders)

@cart.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('Bạn không có quyền truy cập vào đơn hàng này.', 'danger')
        return redirect(url_for('cart.orders'))
    order_items = OrderItem.query.filter_by(order_id=order.id).all()
    return render_template('cart/order_detail.html', title=f'Đơn hàng #{order.id}', order=order,
                           order_items=order_items)

@cart.route('/cancel_order/<int:order_id>', methods=['POST'])
@login_required
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('Bạn không có quyền hủy đơn hàng này.', 'danger')
        return redirect(url_for('cart.orders'))
    if order.status != 'pending':
        flash('Không thể hủy đơn hàng vì đơn hàng không ở trạng thái chờ xử lý.', 'warning')
        return redirect(url_for('cart.order_detail', order_id=order.id))
    order.status = 'cancelled'
    db.session.commit()
    flash('Đơn hàng đã được hủy thành công.', 'success')
    return redirect(url_for('cart.orders'))

@cart.route('/get-addresses', methods=['GET'])
@login_required
def get_addresses():
    addresses = Address.query.filter_by(user_id=current_user.id).all()
    addresses_data = [{
        'id': addr.id,
        'recipient_name': addr.recipient_name,
        'phone': addr.phone,
        'address': addr.address,
        'is_default': addr.is_default
    } for addr in addresses]
    return jsonify({'addresses': addresses_data})