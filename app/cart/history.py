from flask import redirect, url_for

@app.route('/cart/history')
def cart_history():
    return redirect(url_for('order_management.my_orders'))
