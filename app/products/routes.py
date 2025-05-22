from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user, login_required
from app.models import Product, Category, CartItem, Comment, Reaction
from app import db
import logging

products = Blueprint('products', __name__)

# Thiết lập logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@products.route('/products')
def all_products():
    page = request.args.get('page', 1, type=int)
    per_page = 12  # Số sản phẩm mỗi trang

    # Lọc theo danh mục nếu có
    category_slug = request.args.get('category')
    if category_slug:
        category = Category.query.filter_by(slug=category_slug).first_or_404()
        product_list = Product.query.filter_by(category_id=category.id)
        category_name = category.name
    else:
        product_list = Product.query
        category_name = 'Tất cả sản phẩm'

    # Lọc theo giá
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    if min_price:
        product_list = product_list.filter(Product.price >= min_price)
    if max_price:
        product_list = product_list.filter(Product.price <= max_price)

    # Lọc theo nhà sản xuất
    manufacturer = request.args.get('manufacturer')
    if manufacturer:
        product_list = product_list.filter_by(manufacturer=manufacturer)

    # Sắp xếp
    sort = request.args.get('sort', 'default')
    if sort == 'price-asc':
        product_list = product_list.order_by(Product.price.asc())
    elif sort == 'price-desc':
        product_list = product_list.order_by(Product.price.desc())
    elif sort == 'newest':
        product_list = product_list.order_by(Product.created_at.desc())
    elif sort == 'rating':
        product_list = product_list.order_by(Product.rating.desc())

    # Tìm kiếm
    search = request.args.get('search')
    if search:
        search_term = f"%{search}%"
        product_list = product_list.filter(
            (Product.name.ilike(search_term)) |
            (Product.description.ilike(search_term))
        )

    # Phân trang
    products_pagination = product_list.paginate(page=page, per_page=per_page)

    # Lấy tất cả danh mục để hiển thị thanh bên
    categories = Category.query.all()

    # Lấy danh sách các nhà sản xuất để hiển thị bộ lọc
    manufacturers = db.session.query(Product.manufacturer).distinct().all()
    manufacturers = [m[0] for m in manufacturers]

    return render_template('products/products.html',
                           title=category_name,
                           products=products_pagination,
                           categories=categories,
                           manufacturers=manufacturers,
                           current_category=category_slug,
                           current_manufacturer=manufacturer,
                           current_min_price=min_price,
                           current_max_price=max_price,
                           current_sort=sort,
                           search_term=search)

@products.route('/search')
def search():
    """Route tìm kiếm riêng, chuyển hướng đến all_products với tham số tìm kiếm"""
    search_term = request.args.get('search', '')
    return redirect(url_for('products.all_products', search=search_term))

@products.route('/products/<int:product_id>', methods=['GET', 'POST'])
@login_required
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    logger.debug(f"Product ID: {product_id}, Current Rating: {product.rating}")

    # Xử lý gửi đánh giá hoặc bình luận
    if request.method == 'POST':
        if 'content' in request.form:
            content = request.form.get('content')
            parent_id = request.form.get('parent_id')

            # Nếu là đánh giá (có rating)
            if 'rating' in request.form:
                score = int(request.form.get('rating', 0))
                criteria = {
                    'Hiệu năng': int(request.form.get('criteria_hiệu-năng', 0)),
                    'Thời lượng pin': int(request.form.get('criteria_thời-lượng-pin', 0)),
                    'Chất lượng camera': int(request.form.get('criteria_chất-lượng-camera', 0))
                }

                if not content:
                    flash('Vui lòng nhập nội dung bình luận!', 'danger')
                elif score < 1 or score > 5:
                    flash('Điểm đánh giá phải từ 1 đến 5 sao!', 'danger')
                else:
                    comment = Comment(
                        content=content,
                        user_id=current_user.id,
                        product_id=product_id,
                        score=score,
                        criteria=criteria,
                        parent_id=parent_id if parent_id else None
                    )
                    db.session.add(comment)
                    db.session.commit()

                    # Cập nhật rating trung bình của sản phẩm
                    comments_with_score = Comment.query.filter_by(product_id=product_id).filter(Comment.score > 0).all()
                    if comments_with_score:
                        total_score = sum(comment.score for comment in comments_with_score)
                        new_rating = total_score / len(comments_with_score)
                        logger.debug(f"Updating rating: Total Score = {total_score}, Count = {len(comments_with_score)}, New Rating = {new_rating}")
                        product.rating = new_rating
                        try:
                            db.session.commit()
                            logger.debug(f"Rating updated successfully: {product.rating}")
                        except Exception as e:
                            db.session.rollback()
                            logger.error(f"Error updating rating: {str(e)}")
                            flash('Có lỗi khi cập nhật đánh giá!', 'danger')
                    else:
                        logger.debug("No ratings yet, keeping default rating")
                    flash('Đánh giá của bạn đã được gửi!', 'success')

            # Nếu là bình luận hoặc trả lời
            elif content:
                comment = Comment(
                    content=content,
                    user_id=current_user.id,
                    product_id=product_id,
                    parent_id=parent_id if parent_id else None
                )
                db.session.add(comment)
                db.session.commit()
                flash('Bình luận của bạn đã được gửi!', 'success')
            else:
                flash('Vui lòng nhập nội dung bình luận!', 'danger')

            return redirect(url_for('products.product_detail', product_id=product_id))

        # Xử lý reaction
        if 'emoji' in request.form and 'comment_id' in request.form:
            logger.debug(f"Received reaction request: {request.form}")
            emoji = request.form.get('emoji')
            comment_id = request.form.get('comment_id')
            logger.debug(f"Emoji: {emoji}, Comment ID: {comment_id}")
            comment = Comment.query.get(comment_id)

            if not comment:
                logger.error(f"Comment not found: {comment_id}")
                return jsonify({'success': False, 'message': 'Bình luận không tồn tại!'})

            existing_reaction = Reaction.query.filter_by(
                user_id=current_user.id,
                comment_id=comment_id,
                emoji=emoji
            ).first()

            action = None
            count = 0
            if existing_reaction:
                db.session.delete(existing_reaction)
                db.session.commit()
                action = 'removed'
                logger.debug(f"Removed reaction: {emoji} for comment {comment_id}")
            else:
                reaction = Reaction(
                    user_id=current_user.id,
                    comment_id=comment_id,
                    emoji=emoji
                )
                db.session.add(reaction)
                db.session.commit()
                action = 'added'
                logger.debug(f"Added reaction: {emoji} for comment {comment_id}")

            count = Reaction.query.filter_by(comment_id=comment_id, emoji=emoji).count()
            reactions = Reaction.query.filter_by(comment_id=comment_id).all()
            reaction_summary = {}
            for reaction in reactions:
                reaction_summary[reaction.emoji] = reaction_summary.get(reaction.emoji, 0) + 1

            logger.debug(f"Reaction updated: action={action}, count={count}, summary={reaction_summary}")
            return jsonify({
                'success': True,
                'action': action,
                'count': count,
                'reaction_summary': reaction_summary,
                'message': 'Reaction updated!'
            })

    # Lấy các bình luận gốc (không có parent_id)
    comments = Comment.query.filter_by(product_id=product_id, parent_id=None).order_by(Comment.timestamp.desc()).all()

    # Lấy các sản phẩm liên quan
    related_products = Product.query.filter(
        (Product.category_id == product.category_id) &
        (Product.id != product.id)
    ).limit(4).all()

    return render_template('products/product_detail.html',
                           title=product.name,
                           product=product,
                           related_products=related_products,
                           comments=comments)

@products.route('/category/<string:category_slug>')
def category_products(category_slug):
    # Chuyển hướng đến trang sản phẩm với tham số danh mục
    return redirect(url_for('products.all_products', category=category_slug))

@products.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        discounted_price = request.form.get('discounted_price')
        category_id = request.form.get('category_id')
        manufacturer = request.form.get('manufacturer')
        stock_quantity = int(request.form.get('stock_quantity'))
        is_new = 'is_new' in request.form
        is_sale = 'is_sale' in request.form
        image_file = request.files.get('image')

        if not category_id or category_id == "":
            flash('Vui lòng chọn danh mục cho sản phẩm!', 'danger')
            return redirect(url_for('products.add_product'))

        image_path = None
        if image_file and image_file.filename:
            image_path = f"/static/uploads/{image_file.filename}"

        product = Product(
            name=name,
            description=description,
            price=price,
            discounted_price=float(discounted_price) if discounted_price else None,
            category_id=int(category_id),
            manufacturer=manufacturer,
            stock=stock_quantity,  # Sử dụng stock thay vì stock_quantity để khớp với bảng
            is_new=is_new,
            is_sale=is_sale,
            image=image_path
            # Không đặt rating, để MySQL gán DEFAULT 5
        )

        db.session.add(product)
        db.session.commit()

        flash('Thêm sản phẩm thành công!', 'success')
        return redirect(url_for('products.all_products'))

    categories = Category.query.all()
    return render_template('add_product.html', categories=categories)

@products.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.price = float(request.form.get('price'))
        discounted_price = request.form.get('discounted_price')
        category_id = request.form.get('category_id')
        manufacturer = request.form.get('manufacturer')
        stock_quantity = int(request.form.get('stock_quantity'))
        product.is_new = 'is_new' in request.form
        product.is_sale = 'is_sale' in request.form

        if not category_id or category_id == "":
            flash('Vui lòng chọn danh mục cho sản phẩm!', 'danger')
            return redirect(url_for('products.edit_product', product_id=product_id))

        product.category_id = int(category_id)
        product.discounted_price = float(discounted_price) if discounted_price else None
        product.stock = stock_quantity  # Sử dụng stock để khớp với bảng

        image_file = request.files.get('image')
        if image_file and image_file.filename:
            product.image = f"/static/uploads/{image_file.filename}"

        db.session.commit()

        flash('Cập nhật sản phẩm thành công!', 'success')
        return redirect(url_for('products.all_products'))

    categories = Category.query.all()
    return render_template('edit_product.html', product=product, categories=categories)