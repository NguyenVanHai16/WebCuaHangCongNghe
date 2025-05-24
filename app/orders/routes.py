from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Order, OrderStatus
from datetime import datetime

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('/my-orders')
@login_required
def my_orders():
    # Lấy tất cả đơn hàng của người dùng hiện tại, sắp xếp theo thời gian tạo giảm dần
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()

    # Danh sách trạng thái hợp lệ
    status_labels = {
        'pending': 'Chờ xác nhận',
        'confirmed': 'Đã xác nhận',
        'pickup_pending': 'Chờ lấy hàng',
        'shipping': 'Đang giao hàng',
        'delivered': 'Đã giao hàng',
        'cancelled': 'Đã hủy'
    }

    # Tạo dictionary chứa danh sách đơn hàng theo trạng thái
    orders_by_status = {status: [] for status in status_labels}
    for order in orders:
        if order.status in orders_by_status:
            orders_by_status[order.status].append(order)

    # Render template với orders_by_status và status_labels
    return render_template('orders/my_orders.html', title='Đơn mua', orders_by_status=orders_by_status, status_labels=status_labels)

@orders_bp.route('/orders')  # Thêm tuyến đường mới
@login_required
def orders():
    return my_orders()  # Gọi hàm my_orders để sử dụng cùng logic

@orders_bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id and not current_user.is_admin:
        flash('Bạn không có quyền xem đơn hàng này!', 'danger')
        return redirect(url_for('orders.my_orders'))
    return render_template('orders/order_detail.html', order=order)

@orders_bp.route('/orders/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)

    # Kiểm tra xem đơn hàng có phải của user hiện tại hoặc admin không
    if order.user_id != current_user.id and not current_user.is_admin:
        flash('Bạn không có quyền hủy đơn hàng này!', 'danger')
        return redirect(url_for('orders.my_orders'))

    # Kiểm tra xem đơn hàng có thể hủy không
    if order.status != OrderStatus.PENDING.value:
        flash('Chỉ có thể hủy đơn hàng đang chờ xác nhận!', 'danger')
        return redirect(url_for('orders.my_orders'))

    # Cập nhật trạng thái đơn hàng
    order.status = OrderStatus.CANCELLED.value
    order.cancelled_at = datetime.utcnow()
    cancel_reason = request.form.get('cancel_reason')
    if cancel_reason:
        order.cancel_reason = cancel_reason

    # Lưu vào database
    db.session.commit()

    flash('Đơn hàng đã được hủy thành công!', 'success')
    return redirect(url_for('orders.my_orders'))

# Blueprint cho admin
admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Bạn không có quyền truy cập trang này!', 'danger')
        return redirect(url_for('main.index'))

    # Lấy dữ liệu cho các tab
    from app.models import Product, User, Comment
    products = Product.query.all()
    orders = Order.query.all()
    users = User.query.all()
    comments = Comment.query.all()

    return render_template('admin/products.html', products=products, orders=orders, users=users, comments=comments)

@admin_bp.route('/admin/approve_order/<int:order_id>', methods=['POST'])
@login_required
def approve_order(order_id):
    if not current_user.is_admin:
        flash('Bạn không có quyền thực hiện hành động này!', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    order = Order.query.get_or_404(order_id)
    if order.status != OrderStatus.PENDING.value:
        flash('Đơn hàng không ở trạng thái chờ xác nhận!', 'danger')
        return redirect(url_for('admin.admin_dashboard', tab='orders'))

    order.status = OrderStatus.CONFIRMED.value
    order.confirmed_at = datetime.utcnow()
    db.session.commit()

    flash('Đơn hàng đã được xác nhận thành công!', 'success')
    return redirect(url_for('admin.admin_dashboard', tab='orders'))

@admin_bp.route('/admin/update_order_status/<int:order_id>/<string:new_status>', methods=['POST'])
@login_required
def update_order_status(order_id, new_status):
    if not current_user.is_admin:
        flash('Bạn không có quyền thực hiện hành động này!', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    order = Order.query.get_or_404(order_id)
    valid_statuses = ['pending', 'confirmed', 'pickup_pending', 'shipping', 'delivered', 'cancelled']

    if new_status not in valid_statuses:
        flash('Trạng thái không hợp lệ!', 'danger')
        return redirect(url_for('admin.admin_dashboard', tab='orders'))

    # Kiểm tra trạng thái hiện tại và trạng thái mới
    status_flow = {
        'confirmed': ['pickup_pending', 'cancelled'],
        'pickup_pending': ['shipping', 'cancelled'],
        'shipping': ['delivered', 'cancelled'],
        'delivered': [],
        'cancelled': []
    }

    if new_status not in status_flow.get(order.status, []):
        flash('Không thể chuyển đơn hàng sang trạng thái này!', 'danger')
        return redirect(url_for('admin.admin_dashboard', tab='orders'))

    # Cập nhật trạng thái và thời gian tương ứng
    order.status = new_status
    now = datetime.utcnow()
    if new_status == 'pickup_pending':
        order.pickup_at = now
    elif new_status == 'shipping':
        order.shipping_at = now
    elif new_status == 'delivered':
        order.delivered_at = now
    elif new_status == 'cancelled':
        order.cancelled_at = now
        cancel_reason = request.form.get('cancel_reason')
        if cancel_reason:
            order.cancel_reason = cancel_reason

    db.session.commit()

    flash(f'Đơn hàng đã được cập nhật trạng thái thành {get_order_status_label(new_status)}!', 'success')
    return redirect(url_for('admin.admin_dashboard', tab='orders'))

@admin_bp.route('/admin/cancel_order/<int:order_id>', methods=['POST'])
@login_required
def cancel_order_admin(order_id):
    if not current_user.is_admin:
        flash('Bạn không có quyền thực hiện hành động này!', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    order = Order.query.get_or_404(order_id)
    if order.status in [OrderStatus.DELIVERED.value, OrderStatus.CANCELLED.value]:
        flash('Không thể hủy đơn hàng này!', 'danger')
        return redirect(url_for('admin.admin_dashboard', tab='orders'))

    order.status = OrderStatus.CANCELLED.value
    order.cancelled_at = datetime.utcnow()
    cancel_reason = request.form.get('cancel_reason')
    if cancel_reason:
        order.cancel_reason = cancel_reason
    db.session.commit()

    flash('Đơn hàng đã được hủy thành công!', 'success')
    return redirect(url_for('admin.admin_dashboard', tab='orders'))

@admin_bp.route('/admin/delete_order/<int:order_id>', methods=['POST'])
@login_required
def delete_order(order_id):
    if not current_user.is_admin:
        flash('Bạn không có quyền thực hiện hành động này!', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()

    flash('Đơn hàng đã được xóa thành công!', 'success')
    return redirect(url_for('admin.admin_dashboard', tab='orders'))