from app import create_app, db
from datetime import datetime
import pytz
from flask import current_app, g, render_template, url_for, redirect, session
from app.utils import get_current_time
import secrets

app = create_app()

# Cấu hình thư mục upload
app.config['UPLOAD_FOLDER'] = 'app/static/uploads/sanpham'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff', 'tif', 'svg', 'heic', 'heif', 'ico', 'avif'}

# Kiểm tra file hợp lệ
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Định nghĩa bộ lọc format_number
def format_number(value):
    if value is None or value == '':
        return "0"
    try:
        return "{:,.0f}".format(float(value))
    except (ValueError, TypeError):
        return str(value)

app.jinja_env.filters['format_number'] = format_number

# Định nghĩa bộ lọc format_datetime
def format_datetime(value):
    if value is None:
        return ""
    vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    local_time = value.astimezone(vietnam_tz)
    return local_time.strftime('%Y-%m-%d %H:%M:%S')

app.jinja_env.filters['format_datetime'] = format_datetime

# Định nghĩa hàm get_order_status_label
def get_order_status_label(status):
    status_labels = {
        'pending': 'Chờ xác nhận',
        'confirmed': 'Đã xác nhận',
        'pickup_pending': 'Chờ lấy hàng',
        'shipping': 'Đang giao hàng',
        'delivered': 'Đã giao hàng',
        'cancelled': 'Đã hủy'
    }
    return status_labels.get(status, 'Không xác định')

# Đăng ký get_order_status_label như một hàm toàn cục
app.jinja_env.globals['get_order_status_label'] = get_order_status_label

# Giả lập các hàm lấy dữ liệu
def get_cart_items():
    return []

def calculate_total(cart_items):
    return sum(item.subtotal for item in cart_items) if cart_items else 0

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

@app.before_request
def before_request():
    g.request_start_time = get_current_time()
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)

@app.after_request
def after_request(response):
    if hasattr(g, 'request_start_time'):
        elapsed = get_current_time() - g.request_start_time
        current_app.logger.info(
            f'Request processed in {elapsed.total_seconds():.3f} seconds')
    return response

@app.route('/cart')
def cart():
    cart_items = get_cart_items()
    total = calculate_total(cart_items)
    return render_template('cart/cart.html', cart_items=cart_items, total=total)

@app.route('/cart/history')
def cart_history():
    return redirect(url_for('orders.my_orders'))

@app.route('/checkout')
def checkout():
    cart_items = get_cart_items()
    if not cart_items:
        return redirect(url_for('cart'))

    # Xử lý logic thanh toán ở đây
    # ...

    return redirect(url_for('orders.my_orders'))

@app.route('/products')
def all_products():
    pass

@app.route('/')
def index():
    pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)