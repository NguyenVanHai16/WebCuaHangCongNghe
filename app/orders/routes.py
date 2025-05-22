from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Order
from datetime import datetime  # Thêm dòng này vào đầu file

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('/my-orders')
@login_required
def my_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('orders/my_orders.html', orders=orders)

@orders_bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('Bạn không có quyền xem đơn hàng này!', 'danger')
        return redirect(url_for('orders.my_orders'))
    return render_template('orders/order_detail.html', order=order)

# Thêm route mới để hủy đơn hàng
@orders_bp.route('/orders/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)

    # Kiểm tra xem đơn hàng có phải của user hiện tại không
    if order.user_id != current_user.id:
        flash('Bạn không có quyền hủy đơn hàng này!', 'danger')
        return redirect(url_for('orders.my_orders'))

    # Kiểm tra xem đơn hàng có thể hủy không
    if order.status != 'pending':
        flash('Chỉ có thể hủy đơn hàng đang chờ xác nhận!', 'danger')
        return redirect(url_for('orders.my_orders'))

    # Cập nhật trạng thái đơn hàng
    order.status = 'cancelled'
    order.cancelled_at = datetime.utcnow()

    # Lưu vào database
    db.session.commit()

    flash('Đơn hàng đã được hủy thành công!', 'success')
    return redirect(url_for('orders.my_orders'))