from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models import User


class LoginForm(FlaskForm):
    username = StringField('Tên đăng nhập', validators=[DataRequired(message='Trường này là bắt buộc')])
    password = PasswordField('Mật khẩu', validators=[DataRequired(message='Trường này là bắt buộc')])
    remember = BooleanField('Ghi nhớ đăng nhập')
    submit = SubmitField('Đăng nhập')


class RegisterForm(FlaskForm):
    username = StringField('Tên đăng nhập', validators=[
        DataRequired(message='Trường này là bắt buộc'),
        Length(min=3, max=20, message='Tên đăng nhập phải có độ dài từ 3 đến 20 ký tự')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Trường này là bắt buộc'),
        Email(message='Email không hợp lệ')
    ])
    first_name = StringField('Tên', validators=[Length(max=100)])
    last_name = StringField('Họ', validators=[Length(max=100)])
    password = PasswordField('Mật khẩu', validators=[
        DataRequired(message='Trường này là bắt buộc'),
        Length(min=8, message='Mật khẩu phải có ít nhất 8 ký tự')
    ])
    confirm_password = PasswordField('Xác nhận mật khẩu', validators=[
        DataRequired(message='Trường này là bắt buộc'),
        EqualTo('password', message='Mật khẩu xác nhận không khớp')
    ])
    terms = BooleanField('Tôi đồng ý với Điều khoản dịch vụ và Chính sách bảo mật', validators=[
        DataRequired(message='Bạn phải đồng ý với điều khoản để tiếp tục')
    ])
    submit = SubmitField('Đăng ký')

    # Phương thức kiểm tra tên đăng nhập đã tồn tại chưa
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Tên đăng nhập đã tồn tại. Vui lòng chọn tên khác.')

    # Phương thức kiểm tra email đã tồn tại chưa
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email đã được sử dụng. Vui lòng sử dụng email khác.')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Mật khẩu hiện tại', validators=[
        DataRequired(message='Trường này là bắt buộc')
    ])
    new_password = PasswordField('Mật khẩu mới', validators=[
        DataRequired(message='Trường này là bắt buộc'),
        Length(min=8, message='Mật khẩu mới phải có ít nhất 8 ký tự')
    ])
    confirm_password = PasswordField('Xác nhận mật khẩu mới', validators=[
        DataRequired(message='Trường này là bắt buộc'),
        EqualTo('new_password', message='Mật khẩu xác nhận không khớp')
    ])
    submit = SubmitField('Đổi mật khẩu')