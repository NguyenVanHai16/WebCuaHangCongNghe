from app import create_app, db
from datetime import datetime
from flask import current_app, g, render_template
from app.utils import get_current_time

app = create_app()

# Cấu hình thư mục upload
app.config['UPLOAD_FOLDER'] = 'app/static/uploads/sanpham'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Kiểm tra file hợp lệ
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Định nghĩa bộ lọc format_number
def format_number(value):
    return "{:,.0f}".format(value)

app.jinja_env.filters['format_number'] = format_number

# Định nghĩa hàm get_order_status_label
def get_order_status_label(status):
    status_labels = {
        'pending': 'Chờ xử lý',
        'processing': 'Đang xử lý',
        'shipped': 'Đang giao',
        'delivered': 'Đã giao',
        'cancelled': 'Đã hủy'
    }
    return status_labels.get(status, 'Không xác định')

# Đăng ký get_order_status_label như một hàm toàn cục
app.jinja_env.globals['get_order_status_label'] = get_order_status_label

# Giả lập các hàm lấy dữ liệu
def get_cart_items():
    return []  # Thay bằng logic thực tế

def calculate_total(cart_items):
    return sum(item.subtotal for item in cart_items) if cart_items else 0

def get_orders():
    return []  # Thay bằng logic thực tế

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

@app.before_request
def before_request():
    g.request_start_time = get_current_time()

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
    orders = get_orders()
    return render_template('cart/history.html', orders=orders)

@app.route('/cart/update/<int:item_id>', methods=['POST'])
def update_cart(item_id):
    pass

@app.route('/cart/remove/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id):
    pass

@app.route('/checkout')
def checkout():
    pass

@app.route('/products')
def all_products():
    pass

@app.route('/cart/order/<int:order_id>')
def order_detail(order_id):
    pass

@app.route('/')
def index():
    pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)