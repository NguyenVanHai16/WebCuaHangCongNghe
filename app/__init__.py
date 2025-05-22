from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import os

# Khởi tạo SQLAlchemy
db = SQLAlchemy()

# Khởi tạo Flask-Migrate
migrate = Migrate()

def create_app():
    app = Flask(__name__, template_folder='templates')

    # Cấu hình ứng dụng
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'techmart-default-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:12345@localhost/techmart?charset=utf8mb4'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads/sanpham')  # Thêm dòng này
    # Khởi tạo cơ sở dữ liệu
    db.init_app(app)

    # Khởi tạo Migrate với app và db
    migrate.init_app(app, db)

    # Đăng ký các blueprint
    from app.admin.routes import admin_bp
    from app.auth.routes import auth
    from app.main.routes import main
    from app.products.routes import products
    from app.cart.routes import cart
    from app.orders.routes import orders_bp  # Thêm dòng này

    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(products)
    app.register_blueprint(cart)
    app.register_blueprint(orders_bp)  # Thêm dòng này

    # Thiết lập flask-login
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Vui lòng đăng nhập để sử dụng chức năng này.'
    login_manager.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Tạo tất cả các bảng trong cơ sở dữ liệu
    with app.app_context():
        db.create_all()

    return app