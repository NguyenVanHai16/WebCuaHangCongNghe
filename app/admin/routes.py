from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app as app
from flask_login import login_required, current_user
from app import db
from app.models import Order, Product, Category, User, Comment, OrderItem, Reaction, CartItem, Address
from datetime import datetime, timedelta
from functools import wraps
import os
from werkzeug.utils import secure_filename

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Bạn không có quyền truy cập!', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def commit_db_changes(success_message, error_message):
    try:
        db.session.commit()
        flash(success_message, 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'{error_message}: {str(e)}', 'danger')
        print(f"Lỗi xảy ra: {e}")
        raise

def save_image(image_file):
    upload_folder = app.config['UPLOAD_FOLDER']
    print(f"UPLOAD_FOLDER: {upload_folder}")
    if not os.path.exists(upload_folder):
        print(f"Tạo thư mục: {upload_folder}")
        os.makedirs(upload_folder)
    filename = secure_filename(image_file.filename)
    if not filename:
        print("Lỗi: Tên tệp rỗng hoặc không hợp lệ")
        raise ValueError("Tên tệp không hợp lệ")
    image_path = os.path.join(upload_folder, filename)
    print(f"Lưu ảnh vào: {image_path}")
    try:
        image_file.save(image_path)
        print(f"Đã lưu ảnh thành công vào: {image_path}")
    except Exception as e:
        print(f"Lỗi khi lưu ảnh: {str(e)}")
        raise
    return_path = os.path.join('uploads/sanpham', filename).replace('\\', '/')
    print(f"Trả về đường dẫn: {return_path}")
    return return_path

@admin_bp.route('/orders')
@login_required
@admin_required
def orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)

@admin_bp.route('/orders/<int:order_id>')
@login_required
@admin_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html', order=order)

@admin_bp.route('/orders/<int:order_id>/update', methods=['POST'], endpoint='update_order_status')
@login_required
@admin_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    action = request.form.get('action')
    now = datetime.utcnow()

    # Xác thực chuyển đổi trạng thái
    valid_transitions = {
        'confirm': ['pending'],
        'pickup': ['confirmed'],
        'ship': ['pickup_pending'],
        'deliver': ['shipping'],
        'cancel': ['pending', 'confirmed', 'pickup_pending', 'shipping']
    }

    if action not in valid_transitions:
        flash('Hành động không hợp lệ!', 'danger')
        return redirect(url_for('admin.order_detail', order_id=order_id))

    if order.status not in valid_transitions[action]:
        flash(f'Không thể thực hiện hành động "{action}" từ trạng thái hiện tại "{order.status}"!', 'danger')
        return redirect(url_for('admin.order_detail', order_id=order_id))

    if action == 'confirm':
        order.status = 'confirmed'
        order.confirmed_at = now
        order.estimated_delivery = now + timedelta(days=3)
        success_message = 'Đơn hàng đã được xác nhận!'
        error_message = 'Có lỗi xảy ra khi xác nhận đơn hàng'
    elif action == 'pickup':
        order.status = 'pickup_pending'
        order.pickup_at = now
        success_message = 'Đơn hàng đã chuyển sang trạng thái chờ lấy hàng!'
        error_message = 'Có lỗi xảy ra khi cập nhật trạng thái chờ lấy hàng'
    elif action == 'ship':
        order.status = 'shipping'
        order.shipping_at = now
        success_message = 'Đơn hàng đã bắt đầu giao!'
        error_message = 'Có lỗi xảy ra khi cập nhật trạng thái giao hàng'
    elif action == 'deliver':
        order.status = 'delivered'
        order.delivered_at = now
        success_message = 'Đơn hàng đã giao thành công!'
        error_message = 'Có lỗi xảy ra khi cập nhật trạng thái giao hàng thành công'
    elif action == 'cancel':
        order.status = 'cancelled'
        order.cancelled_at = now
        cancel_reason = request.form.get('cancel_reason')
        if cancel_reason:
            order.cancel_reason = cancel_reason
        success_message = 'Đã hủy đơn hàng thành công!'
        error_message = 'Có lỗi xảy ra khi hủy đơn hàng'
    else:
        flash('Hành động không hợp lệ!', 'danger')
        return redirect(url_for('admin.order_detail', order_id=order_id))

    commit_db_changes(success_message, error_message)
    return redirect(url_for('admin.order_detail', order_id=order_id))

@admin_bp.route('/orders/<int:order_id>/update-delivery', methods=['POST'])
@login_required
@admin_required
def admin_update_delivery(order_id):
    order = Order.query.get_or_404(order_id)
    estimated_date = request.form.get('estimated_date')
    estimated_time = request.form.get('estimated_time')

    if not estimated_date or not estimated_time:
        flash('Vui lòng nhập đầy đủ thông tin thời gian dự kiến!', 'danger')
        return redirect(url_for('admin.order_detail', order_id=order_id))

    try:
        estimated_delivery = datetime.strptime(f"{estimated_date} {estimated_time}", "%Y-%m-%d %H:%M")
        order.estimated_delivery = estimated_delivery
        commit_db_changes('Đã cập nhật thời gian dự kiến giao hàng!', 'Có lỗi xảy ra khi cập nhật thời gian dự kiến')
    except ValueError as e:
        flash(f'Định dạng thời gian không hợp lệ: {str(e)}', 'danger')
        return redirect(url_for('admin.order_detail', order_id=order_id))

    return redirect(url_for('admin.order_detail', id=order_id))

@admin_bp.route('/products')
@login_required
@admin_required
def list_products():
    products = Product.query.all()
    orders = Order.query.order_by(Order.created_at.desc()).all()
    users = User.query.all()
    comments = Comment.query.order_by(Comment.timestamp.desc()).all()
    return render_template('admin/products.html', products=products, orders=orders, users=users, comments=comments)

@admin_bp.route('/add_product', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price_input = request.form.get('price')
        discounted_price_input = request.form.get('discounted_price')
        category_id = request.form.get('category_id')
        manufacturer = request.form.get('manufacturer')
        stock_quantity_input = request.form.get('stock_quantity')
        is_new = 'is_new' in request.form
        is_sale = 'is_sale' in request.form
        image_file = request.files.get('image')
        print(f"Thêm sản phẩm - Tệp ảnh: {image_file}, Tên tệp: {image_file.filename if image_file else 'None'}")  # Debug

        if not name or not description or not price_input or not manufacturer:
            flash('Vui lòng cung cấp đầy đủ thông tin bắt buộc!', 'danger')
            print("Lỗi: Thiếu thông tin trường bắt buộc")
            return redirect(url_for('admin.add_product'))

        if not category_id or category_id == "":
            flash('Vui lòng chọn danh mục sản phẩm!', 'danger')
            print("Lỗi: Chưa chọn danh mục")
            return redirect(url_for('admin.add_product'))

        try:
            price = float(price_input)
            discounted_price = float(discounted_price_input) if discounted_price_input else None
            stock_quantity = int(stock_quantity_input) if stock_quantity_input else 0

            if price <= 0 or (discounted_price and discounted_price <= 0):
                flash('Giá sản phẩm phải lớn hơn 0!', 'danger')
                print("Lỗi: Giá không hợp lệ")
                return redirect(url_for('admin.add_product'))
            if stock_quantity < 0:
                flash('Số lượng tồn kho không thể âm!', 'danger')
                print("Lỗi: Số lượng tồn kho âm")
                return redirect(url_for('admin.add_product'))
        except ValueError as e:
            flash(f'Giá hoặc số lượng không hợp lệ: {str(e)}', 'danger')
            print(f"Lỗi: Giá hoặc số lượng không hợp lệ: {str(e)}")
            return redirect(url_for('admin.add_product'))

        image_path = None
        if image_file and image_file.filename:
            try:
                image_path = save_image(image_file)
                print(f"Đã cập nhật product.image thành: {image_path}")
            except Exception as e:
                flash(f'Có lỗi khi lưu hình ảnh: {str(e)}', 'danger')
                print(f"Lỗi khi lưu ảnh: {str(e)}")
                return redirect(url_for('admin.add_product'))

        product = Product(
            name=name,
            description=description,
            price=price,
            discounted_price=discounted_price,
            category_id=int(category_id),
            manufacturer=manufacturer,
            stock=stock_quantity,
            is_new=is_new,
            is_sale=is_sale,
            image=image_path or "uploads/sanpham/default.jpg"
        )

        db.session.add(product)
        commit_db_changes('Thêm sản phẩm thành công!', 'Có lỗi xảy ra khi thêm sản phẩm')
        return redirect(url_for('admin.list_products', tab='products'))

    categories = Category.query.all()
    return render_template('admin/add_product.html', categories=categories)

@admin_bp.route('/edit_product/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(id):
    product = Product.query.get_or_404(id)

    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        price_input = request.form.get('price')
        discounted_price_input = request.form.get('discounted_price')
        category_id = request.form.get('category_id')
        manufacturer = request.form.get('manufacturer')
        stock_quantity_input = request.form.get('stock')
        product.is_new = 'is_new' in request.form
        product.is_sale = 'is_sale' in request.form

        if not product.name or not product.description or not price_input or not manufacturer:
            flash('Vui lòng cung cấp đầy đủ thông tin bắt buộc!', 'danger')
            print("Lỗi: Thiếu thông tin trường bắt buộc")
            return redirect(url_for('admin.edit_product', id=product.id))

        if not category_id or category_id == "":
            flash('Vui lòng chọn danh mục sản phẩm!', 'danger')
            print("Lỗi: Chưa chọn danh mục")
            return redirect(url_for('admin.edit_product', id=product.id))

        try:
            product.price = float(price_input)
            product.discounted_price = float(discounted_price_input) if discounted_price_input else None
            new_stock = int(stock_quantity_input) if stock_quantity_input else 0

            if product.price <= 0 or (product.discounted_price and product.discounted_price <= 0):
                flash('Giá sản phẩm phải lớn hơn 0!', 'danger')
                print("Lỗi: Giá không hợp lệ")
                return redirect(url_for('admin.edit_product', id=product.id))
            if new_stock < 0:
                flash('Số lượng tồn kho không thể âm!', 'danger')
                print("Lỗi: Số lượng tồn kho âm")
                return redirect(url_for('admin.edit_product', id=product.id))

            order_items = OrderItem.query.filter_by(product_id=product.id).join(Order).filter(Order.status.in_(['pending', 'confirmed', 'pickup_pending', 'shipping'])).all()
            total_ordered_quantity = sum(item.quantity for item in order_items)

            if new_stock < total_ordered_quantity:
                flash(f'Số lượng tồn kho mới ({new_stock}) nhỏ hơn tổng số lượng trong các đơn hàng đang xử lý ({total_ordered_quantity}). Vui lòng kiểm tra lại!', 'danger')
                print(f"Lỗi: Số lượng tồn kho mới {new_stock} nhỏ hơn số lượng đơn hàng đang xử lý {total_ordered_quantity}")
                return redirect(url_for('admin.edit_product', id=product.id))

            product.stock = new_stock
            product.category_id = int(category_id)

            image_file = request.files.get('image')
            print(f"Chỉnh sửa sản phẩm - Tệp ảnh: {image_file}, Tên tệp: {image_file.filename if image_file else 'None'}")  # Debug
            if image_file and image_file.filename:
                try:
                    product.image = save_image(image_file)
                    print(f"Đã cập nhật product.image thành: {product.image}")
                except Exception as e:
                    flash(f'Có lỗi khi lưu hình ảnh: {str(e)}', 'danger')
                    print(f"Lỗi khi lưu ảnh: {str(e)}")
                    return redirect(url_for('admin.edit_product', id=product.id))

            commit_db_changes('Cập nhật sản phẩm thành công!', 'Có lỗi xảy ra khi cập nhật sản phẩm')
            return redirect(url_for('admin.list_products', tab='products'))

        except ValueError as e:
            flash(f'Giá hoặc số lượng không hợp lệ: {str(e)}', 'danger')
            print(f"Lỗi: Giá hoặc số lượng không hợp lệ: {str(e)}")
            return redirect(url_for('admin.edit_product', id=product.id))

    categories = Category.query.all()
    return render_template('admin/edit_product.html', product=product, categories=categories)

@admin_bp.route('/delete_product/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    Comment.query.filter_by(product_id=product.id).delete()
    OrderItem.query.filter_by(product_id=product.id).delete()
    CartItem.query.filter_by(product_id=product.id).delete()
    db.session.delete(product)
    commit_db_changes('Xóa sản phẩm thành công!', 'Có lỗi xảy ra khi xóa sản phẩm')
    return redirect(url_for('admin.list_products', tab='products'))

@admin_bp.route('/cancel_order/<int:order_id>', methods=['POST'])
@login_required
@admin_required
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.status != 'pending':
        flash('Đơn hàng không ở trạng thái chờ duyệt!', 'danger')
        return redirect(url_for('admin.list_products', tab='orders'))
    cancel_reason = request.form.get('cancel_reason')
    if not cancel_reason:
        flash('Vui lòng nhập lý do hủy!', 'danger')
        return redirect(url_for('admin.list_products', tab='orders'))
    order.status = 'cancelled'
    order.cancelled_at = datetime.utcnow()
    order.cancel_reason = cancel_reason
    commit_db_changes('Đã hủy đơn hàng thành công!', 'Có lỗi xảy ra khi hủy đơn hàng')
    return redirect(url_for('admin.list_products', tab='orders'))

@admin_bp.route('/approve_order/<int:order_id>', methods=['POST'])
@login_required
@admin_required
def approve_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.status != 'pending':
        flash('Đơn hàng không ở trạng thái chờ duyệt!', 'danger')
        return redirect(url_for('admin.list_products', tab='orders'))
    order.status = 'confirmed'
    order.confirmed_at = datetime.utcnow()
    order.estimated_delivery = datetime.utcnow() + timedelta(days=3)
    commit_db_changes('Đã duyệt đơn hàng thành công!', 'Có lỗi xảy ra khi duyệt đơn hàng')
    return redirect(url_for('admin.list_products', tab='orders'))

@admin_bp.route('/delete_order/<int:order_id>', methods=['POST'])
@login_required
@admin_required
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    OrderItem.query.filter_by(order_id=order.id).delete()
    db.session.delete(order)
    commit_db_changes('Đã xóa đơn hàng thành công!', 'Có lỗi xảy ra khi xóa đơn hàng')
    return redirect(url_for('admin.list_products', tab='orders'))

@admin_bp.route('/edit_user/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(id):
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        role = request.form.get('role')
        if not user.username or not user.email:
            flash('Tên người dùng và email không được để trống!', 'danger')
            return redirect(url_for('admin.edit_user', id=user.id))
        if role in ['admin', 'user']:
            user.role = role
        else:
            flash('Vai trò không hợp lệ!', 'danger')
            return redirect(url_for('admin.list_products', tab='users'))
        commit_db_changes('Cập nhật người dùng thành công!', 'Có lỗi xảy ra khi cập nhật người dùng')
        return redirect(url_for('admin.list_products', tab='users'))
    return render_template('admin/edit_user.html', user=user)

@admin_bp.route('/delete_user/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('Bạn không thể xóa chính mình!', 'danger')
        return redirect(url_for('admin.list_products', tab='users'))
    CartItem.query.filter_by(user_id=user.id).delete()
    Address.query.filter_by(user_id=user.id).delete()
    Comment.query.filter_by(user_id=user.id).delete()
    Reaction.query.filter_by(user_id=user.id).delete()
    Order.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    commit_db_changes('Xóa người dùng thành công!', 'Có lỗi xảy ra khi xóa người dùng')
    return redirect(url_for('admin.list_products', tab='users'))

@admin_bp.route('/edit_comment/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_comment(id):
    comment = Comment.query.get_or_404(id)
    if request.method == 'POST':
        comment.content = request.form.get('content')
        score_input = request.form.get('score')
        if not comment.content:
            flash('Nội dung bình luận không được để trống!', 'danger')
            return redirect(url_for('admin.edit_comment', id=comment.id))
        if score_input:
            try:
                score = int(score_input)
                if 1 <= score <= 5:
                    comment.score = score
                else:
                    flash('Điểm đánh giá phải từ 1 đến 5!', 'danger')
                    return redirect(url_for('admin.list_products', tab='comments'))
            except ValueError:
                flash('Điểm đánh giá không hợp lệ!', 'danger')
                return redirect(url_for('admin.list_products', tab='comments'))
        commit_db_changes('Cập nhật bình luận thành công!', 'Có lỗi xảy ra khi cập nhật bình luận')
        return redirect(url_for('admin.list_products', tab='comments'))
    return render_template('admin/edit_comment.html', comment=comment)

@admin_bp.route('/delete_comment/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_comment(id):
    comment = Comment.query.get_or_404(id)
    Reaction.query.filter_by(comment_id=comment.id).delete()
    db.session.delete(comment)
    commit_db_changes('Xóa bình luận thành công!', 'Có lỗi xảy ra khi xóa bình luận')
    return redirect(url_for('admin.list_products', tab='comments'))