from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User, Address, Order
from app import db
from app.auth.forms import LoginForm, RegisterForm
import secrets
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import os

auth = Blueprint('auth', __name__)

# Hàm gửi email (sử dụng biến môi trường cho thông tin SMTP)
def send_reset_email(user, token):
    sender = os.getenv('EMAIL_USER', 'your-email@example.com')
    receiver = user.email
    subject = "TechMart - Yêu cầu đặt lại mật khẩu"
    reset_link = url_for('auth.reset_password', token=token, _external=True)
    body = f"""
     Bạn đã yêu cầu đặt lại mật khẩu cho tài khoản TechMart của mình.
     Vui lòng nhấp vào liên kết sau để đặt lại mật khẩu: {reset_link}
     Liên kết này sẽ hết hạn sau 30 phút.
     Nếu bạn không thực hiện yêu cầu này, vui lòng bỏ qua email này.
     """

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender, os.getenv('EMAIL_PASSWORD', 'your-email-password'))
            server.sendmail(sender, receiver, msg.as_string())
        return True
    except smtplib.SMTPException as e:
        print(f"Error sending email: {e}")
        return False

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        print(f"User found: {user}")
        print(f"Password entered: {form.password.data}")
        print(f"Password match: {user and user.check_password(form.password.data)}")  # Sửa: Dùng user.check_password thay vì check_password_hash(user.password, ...)
        if user and user.check_password(form.password.data):  # Sửa: Dùng user.check_password thay vì check_password_hash(user.password, ...)
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('main.index'))
        else:
            flash('Đăng nhập không thành công. Vui lòng kiểm tra lại tên đăng nhập và mật khẩu.', 'danger')

    return render_template('auth/login.html', form=form, title='Đăng nhập')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter((User.username == form.username.data) |
                                          (User.email == form.email.data)).first()
        if existing_user:
            flash('Tên đăng nhập hoặc email đã tồn tại.', 'danger')
            return render_template('auth/register.html', form=form, title='Đăng ký')

        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role='admin' if form.username.data == 'admin_user' else 'user'
        )
        user.set_password(form.password.data)  # Băm mật khẩu khi đăng ký
        db.session.add(user)
        db.session.commit()

        flash('Đăng ký thành công! Bạn có thể đăng nhập ngay bây giờ.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form, title='Đăng ký')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Bạn đã đăng xuất thành công.', 'info')
    return redirect(url_for('main.index'))

@auth.route('/profile')
@login_required
def profile():
    addresses = Address.query.filter_by(user_id=current_user.id).all()
    recent_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).limit(5).all()

    def get_order_status_label(status):
        status_labels = {
            'pending': 'Chờ xác nhận',
            'confirmed': 'Đã xác nhận',
            'shipping': 'Đang giao hàng',
            'delivered': 'Đã giao hàng',
            'cancelled': 'Đã hủy'
        }
        return status_labels.get(status, 'Không xác định')

    return render_template('auth/profile.html',
                           title='Thông tin tài khoản',
                           addresses=addresses,
                           recent_orders=recent_orders,
                           get_order_status_label=get_order_status_label)

@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not current_user.check_password(current_password):  # Sửa: Dùng current_user.check_password thay vì check_password_hash(current_user.password, ...)
            flash('Mật khẩu hiện tại không đúng.', 'error')
            return redirect(url_for('auth.change_password'))

        if new_password != confirm_password:
            flash('Mật khẩu xác nhận không khớp với mật khẩu mới.', 'error')
            return redirect(url_for('auth.change_password'))

        current_user.set_password(new_password)  # Băm mật khẩu mới
        db.session.commit()

        flash('Đổi mật khẩu thành công!', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('auth/change_password.html', title='Đổi mật khẩu')

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()

        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expiry = datetime.utcnow() + timedelta(minutes=30)
            db.session.commit()

            if send_reset_email(user, token):
                flash('Liên kết đặt lại mật khẩu đã được gửi đến email của bạn.', 'success')
            else:
                flash('Có lỗi xảy ra khi gửi email. Vui lòng thử lại sau.', 'error')
        else:
            flash('Email này không tồn tại.', 'error')

        return redirect(url_for('auth.login'))

    return redirect(url_for('auth.login'))

@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    user = User.query.filter_by(reset_token=token).first()

    if not user or user.reset_token_expiry < datetime.utcnow():
        flash('Liên kết đặt lại mật khẩu không hợp lệ hoặc đã hết hạn.', 'error')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            flash('Mật khẩu xác nhận không khớp với mật khẩu mới.', 'error')
            return redirect(url_for('auth.reset_password', token=token))

        user.set_password(new_password)  # Băm mật khẩu mới
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()

        flash('Đặt lại mật khẩu thành công! Vui lòng đăng nhập.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token, title='Đặt lại mật khẩu')

@auth.route('/add-address', methods=['POST'])
@login_required
def add_address():
    if request.method == 'POST':
        recipient_name = request.form.get('recipient_name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        is_default = 'true' in request.form.get('is_default', '').lower()

        if is_default:
            addresses = Address.query.filter_by(user_id=current_user.id, is_default=True).all()
            for addr in addresses:
                addr.is_default = False

        new_address = Address(
            user_id=current_user.id,
            recipient_name=recipient_name,
            phone=phone,
            address=address,
            is_default=is_default
        )

        db.session.add(new_address)
        db.session.commit()

        flash('Thêm địa chỉ thành công!', 'success')
        return redirect(url_for('auth.profile'))

    return redirect(url_for('auth.profile'))

@auth.route('/get-address/<int:address_id>', methods=['GET'])
@login_required
def get_address(address_id):
    address = Address.query.filter_by(id=address_id, user_id=current_user.id).first()

    if not address:
        return jsonify({"error": "Không tìm thấy địa chỉ"}), 404

    return jsonify({
        "id": address.id,
        "recipient_name": address.recipient_name,
        "phone": address.phone,
        "address": address.address,
        "is_default": address.is_default
    })

@auth.route('/update-address/<int:address_id>', methods=['POST'])
@login_required
def update_address(address_id):
    address = Address.query.filter_by(id=address_id, user_id=current_user.id).first()

    if not address:
        flash('Không tìm thấy địa chỉ.', 'error')
        return redirect(url_for('auth.profile'))

    recipient_name = request.form.get('recipient_name')
    phone = request.form.get('phone')
    address_text = request.form.get('address')
    is_default = 'true' in request.form.get('is_default', '').lower()

    if is_default:
        addresses = Address.query.filter_by(user_id=current_user.id, is_default=True).all()
        for addr in addresses:
            if addr.id != address_id:
                addr.is_default = False

    address.recipient_name = recipient_name
    address.phone = phone
    address.address = address_text
    address.is_default = is_default

    db.session.commit()

    flash('Cập nhật địa chỉ thành công!', 'success')
    return redirect(url_for('auth.profile'))

@auth.route('/delete-address/<int:address_id>', methods=['POST'])
@login_required
def delete_address(address_id):
    address = Address.query.filter_by(id=address_id, user_id=current_user.id).first()

    if not address:
        flash('Không tìm thấy địa chỉ.', 'error')
        return redirect(url_for('auth.profile'))

    was_default = address.is_default
    db.session.delete(address)

    if was_default:
        remaining_address = Address.query.filter_by(user_id=current_user.id).first()
        if remaining_address:
            remaining_address.is_default = True

    db.session.commit()

    flash('Đã xóa địa chỉ thành công!', 'success')
    return redirect(url_for('auth.profile'))

@auth.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')

        existing_user = User.query.filter(User.email == email, User.id != current_user.id).first()
        if existing_user:
            flash('Email này đã được sử dụng bởi người dùng khác.', 'error')
            return redirect(url_for('auth.profile'))

        current_user.email = email
        current_user.first_name = first_name
        current_user.last_name = last_name

        db.session.commit()

        flash('Cập nhật thông tin thành công!', 'success')
        return redirect(url_for('auth.profile'))

    return redirect(url_for('auth.profile'))