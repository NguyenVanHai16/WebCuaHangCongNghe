from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user, login_required
from app.models import Product, Category, CartItem, Comment, Reaction, User
from app import db
from sqlalchemy.orm import joinedload
import logging

products = Blueprint('products', __name__)

# Thiết lập logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@products.route('/test_endpoint', methods=['GET'])
def test_endpoint():
    logger.debug("Test endpoint accessed")
    return jsonify({'success': True, 'message': 'Products blueprint is working'})

@products.route('/products')
def all_products():
    page = request.args.get('page', 1, type=int)
    per_page = 12  # Số sản phẩm mỗi trang

    # Khởi tạo truy vấn cơ bản
    product_list = Product.query

    # Tìm kiếm (ưu tiên áp dụng đầu tiên)
    search = request.args.get('search')
    search_term = None
    if search:
        search_term = f"%{search.strip()}%"
        product_list = product_list.filter(
            (Product.name.ilike(search_term)) |
            (Product.description.ilike(search_term)) |
            (Product.manufacturer.ilike(search_term))
        )
        logger.debug(f"Search term: {search}, Matched products: {product_list.count()}")

    # Lọc theo danh mục
    category_slug = request.args.get('category')
    category_name = 'Tất cả sản phẩm'
    if category_slug:
        category = Category.query.filter_by(slug=category_slug).first_or_404()
        product_list = product_list.filter_by(category_id=category.id)
        category_name = category.name

    # Lọc theo nhà sản xuất
    manufacturer = request.args.get('manufacturer')
    if manufacturer:
        product_list = product_list.filter_by(manufacturer=manufacturer)

    # Lọc theo giá
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    if min_price:
        product_list = product_list.filter(Product.price >= min_price)
    if max_price:
        product_list = product_list.filter(Product.price <= max_price)

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

    # Phân trang
    try:
        products_pagination = product_list.paginate(page=page, per_page=per_page, error_out=False)
        logger.debug(f"Page: {page}, Total products: {products_pagination.total}, Items: {len(products_pagination.items)}")
    except Exception as e:
        logger.error(f"Pagination error: {str(e)}")
        products_pagination = product_list.paginate(page=1, per_page=per_page, error_out=False)

    # Gán is_liked cho từng sản phẩm
    if current_user.is_authenticated:
        liked_product_ids = {product.id for product in current_user.likes}
        for product in products_pagination.items:
            product.is_liked = product.id in liked_product_ids
    else:
        for product in products_pagination.items:
            product.is_liked = False

    # Lấy tất cả danh mục để hiển thị thanh bên
    categories = Category.query.all()

    # Lấy danh sách các nhà sản xuất để hiển thị bộ lọc
    manufacturers = db.session.query(Product.manufacturer).distinct().all()
    manufacturers = [m[0] for m in manufacturers if m[0]]

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
    search_term = request.args.get('search', '').strip()
    return redirect(url_for('products.all_products', search=search_term))

@products.route('/products/<int:product_id>', methods=['GET', 'POST'])
@login_required
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    logger.debug(f"Product ID: {product_id}, Current Rating: {product.rating}")

    if request.method == 'POST':
        try:
            # Xử lý thả/xóa biểu tượng (reaction)
            if 'emoji' in request.form and 'comment_id' in request.form:
                emoji = request.form.get('emoji')
                comment_id = int(request.form.get('comment_id'))
                logger.debug(f"Received reaction request: emoji={emoji}, comment_id={comment_id}, user_id={current_user.id}")

                # Kiểm tra comment_id có tồn tại không
                comment = Comment.query.get(comment_id)
                if not comment:
                    logger.error(f"Comment {comment_id} not found")
                    return jsonify({
                        'success': False,
                        'message': 'Bình luận không tồn tại!'
                    }), 404

                # Kiểm tra user_id có tồn tại không
                user = User.query.get(current_user.id)
                if not user:
                    logger.error(f"User {current_user.id} not found")
                    return jsonify({
                        'success': False,
                        'message': 'Người dùng không tồn tại!'
                    }), 404

                # Xóa tất cả các biểu tượng cũ của người dùng cho bình luận này
                existing_reactions = Reaction.query.filter_by(
                    user_id=current_user.id,
                    comment_id=comment_id
                ).all()
                for reaction in existing_reactions:
                    db.session.delete(reaction)

                # Thêm biểu tượng mới
                action = 'added'
                reaction = Reaction(
                    user_id=current_user.id,
                    comment_id=comment_id,
                    emoji=emoji
                )
                db.session.add(reaction)
                db.session.commit()
                logger.debug(f"Added reaction: {emoji} for comment {comment_id}")

                # Tính reaction_summary
                reactions = Reaction.query.filter_by(comment_id=comment_id).all()
                reaction_summary = {}
                for reaction in reactions:
                    emoji = reaction.emoji
                    reaction_summary[emoji] = reaction_summary.get(emoji, 0) + 1

                count = reaction_summary.get(emoji, 0)
                logger.debug(f"Reaction updated: action={action}, count={count}, summary={reaction_summary}")
                return jsonify({
                    'success': True,
                    'action': action,
                    'count': count,
                    'reaction_summary': reaction_summary,
                    'reaction_emoji': emoji,
                    'message': 'Phản ứng đã được cập nhật!'
                })

            # Xử lý đánh giá hoặc bình luận
            if 'content' in request.form:
                content = request.form.get('content')
                parent_id = request.form.get('parent_id')
                logger.debug(f"Received comment/reply request: content={content}, parent_id={parent_id}, user_id={current_user.id}")

                # Nếu là đánh giá (có rating)
                if 'rating' in request.form:
                    try:
                        score = int(request.form.get('rating', 0))
                    except ValueError:
                        logger.error(f"Invalid rating value: {request.form.get('rating')}")
                        return jsonify({
                            'success': False,
                            'message': 'Điểm đánh giá phải là số từ 1 đến 5!'
                        }), 400

                    criteria = {
                        'Hiệu năng': int(request.form.get('criteria_hiệu-năng', 0)),
                        'Thời lượng pin': int(request.form.get('criteria_thời-lượng-pin', 0)),
                        'Chất lượng camera': int(request.form.get('criteria_chất-lượng-camera', 0))
                    }
                    logger.debug(f"POST data: content={content}, score={score}, criteria={criteria}, parent_id={parent_id}")

                    if not content:
                        return jsonify({
                            'success': False,
                            'message': 'Vui lòng nhập nội dung bình luận!'
                        }), 400
                    if score < 1 or score > 5:
                        return jsonify({
                            'success': False,
                            'message': 'Điểm đánh giá phải từ 1 đến 5 sao!'
                        }), 400

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
                        db.session.commit()

                    return jsonify({
                        'success': True,
                        'message': 'Đánh giá của bạn đã được gửi!',
                        'comment': {
                            'id': comment.id,
                            'content': comment.content,
                            'user': {
                                'first_name': current_user.first_name if current_user.first_name else 'Người dùng',
                                'id': current_user.id
                            },
                            'timestamp': comment.timestamp.strftime('%d/%m/%Y') if comment.timestamp else 'N/A',
                            'score': comment.score,
                            'parent_id': comment.parent_id,
                            'reactions': []
                        }
                    })

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
                    logger.debug(f"Added comment/reply: content={content}, parent_id={parent_id}")

                    return jsonify({
                        'success': True,
                        'message': 'Bình luận của bạn đã được gửi!',
                        'comment': {
                            'id': comment.id,
                            'content': comment.content,
                            'user': {
                                'first_name': current_user.first_name if current_user.first_name else 'Người dùng',
                                'id': current_user.id
                            },
                            'timestamp': comment.timestamp.strftime('%d/%m/%Y') if comment.timestamp else 'N/A',
                            'score': 0,
                            'parent_id': comment.parent_id,
                            'reactions': []
                        }
                    })

                else:
                    return jsonify({
                        'success': False,
                        'message': 'Vui lòng nhập nội dung bình luận!'
                    }), 400

            return jsonify({
                'success': False,
                'message': 'Yêu cầu không hợp lệ!'
            }), 400

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error processing POST request: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Lỗi server: {str(e)}'
            }), 500

    # Lấy tất cả bình luận cho sản phẩm
    all_comments = Comment.query.filter_by(product_id=product_id)\
        .options(joinedload(Comment.user), joinedload(Comment.replies).joinedload(Comment.user), joinedload(Comment.reactions))\
        .order_by(Comment.timestamp.desc())\
        .all()

    # Lọc các bình luận cấp cao nhất
    top_level_comments = [comment for comment in all_comments if comment.parent_id is None]

    logger.debug(f"Top-level comments: {[c.id for c in top_level_comments]}")
    for comment in all_comments:
        logger.debug(f"Comment {comment.id} has replies: {[r.id for r in comment.replies]}")

    # Lấy các sản phẩm liên quan
    related_products = Product.query.filter(
        (Product.category_id == product.category_id) &
        (Product.id != product.id)
    ).limit(4).all()

    return render_template('products/product_detail.html',
                           title=product.name,
                           product=product,
                           related_products=related_products,
                           comments=top_level_comments)

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
            image_path = f"/static/uploads/sanpham/{image_file.filename}"

        product = Product(
            name=name,
            description=description,
            price=price,
            discounted_price=float(discounted_price) if discounted_price else None,
            category_id=int(category_id),
            manufacturer=manufacturer,
            stock=stock_quantity,
            is_new=is_new,
            is_sale=is_sale,
            image=image_path
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
        product.stock = stock_quantity

        image_file = request.files.get('image')
        if image_file and image_file.filename:
            product.image = f"/static/uploads/sanpham/{image_file.filename}"

        db.session.commit()

        flash('Cập nhật sản phẩm thành công!', 'success')
        return redirect(url_for('products.all_products'))

    categories = Category.query.all()
    return render_template('edit_product.html', product=product, categories=categories)

@products.route('/like_product/<int:product_id>', methods=['POST'])
def like_product(product_id):
    logger.debug(f"Received request to like_product for product_id: {product_id}")
    if not current_user.is_authenticated:
        logger.debug("User not authenticated, returning JSON error")
        return jsonify({
            'success': False,
            'message': 'Vui lòng đăng nhập để thích sản phẩm!'
        }), 401

    try:
        product = Product.query.get_or_404(product_id)
        data = request.get_json()
        logger.debug(f"Received like request for product {product_id}: {data}")
        liked = data.get('liked')

        if liked is None:
            logger.error("Missing 'liked' field in request")
            return jsonify({'success': False, 'message': "Thiếu trường 'liked' trong yêu cầu"}), 400

        if liked:
            if product not in current_user.likes:
                current_user.likes.append(product)
                logger.debug(f"User {current_user.id} liked product {product_id}")
        else:
            if product in current_user.likes:
                current_user.likes.remove(product)
                logger.debug(f"User {current_user.id} unliked product {product_id}")

        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error processing like request for product {product_id}: {str(e)}")
        return jsonify({'success': False, 'message': f'Lỗi server: {str(e)}'}), 500