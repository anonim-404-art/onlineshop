from flask import Flask, render_template, url_for, redirect, request, session, jsonify
from sqlalchemy.orm import relationship
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import *
from flask_migrate import Migrate
from countryinfo import CountryInfo
from collections import defaultdict
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '123')
DB_HOST = os.getenv('DB_HOST', 'localhost:5432')
DB_NAME = os.getenv('DB_NAME', 'main')
database_path = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
app.config['SQLALCHEMY_DATABASE_URI'] = database_path
app.config['SECRET_KEY'] = "hvyfxrreytg4t846iviv59g97v5vu"
db = SQLAlchemy(app)
Migrate(app, db)


class User(db.Model):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    surname = Column(String)
    email = Column(String)
    password = Column(String)
    role = Column(String)
    checkout = relationship("Checkout", backref="user", order_by="Checkout.id")
    request = relationship("Request", backref="user", order_by="Request.id")
    product = relationship("Product", backref="user", secondary="store", order_by="Product.id")


class Checkout(db.Model):
    __tablename__ = "checkout"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    surname = Column(String)
    company_name = Column(String)
    country = Column(String)
    street_address_1 = Column(String)
    street_address_2 = Column(String)
    town = Column(String)
    state = Column(String)
    zip_code = Column(Integer)
    number = Column(Integer)


class Product(db.Model):
    __tablename__ = "product"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    wishlist = relationship("Wishlist", backref="product", order_by="Wishlist.id")
    name = Column(String)
    brand = Column(String)
    price = Column(Float)
    description = Column(String)
    images = Column(String)
    back_image = Column(String)
    side_image = Column(String)
    bottom_image = Column(String)
    just_image = Column(String)
    colors = Column(JSON)
    category = Column(String)
    date = Column(String)


class Request(db.Model):
    __tablename__ = "request"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))


class Order(db.Model):
    __tablename__ = "order"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    product_id = Column(JSON)
    date = Column(String)
    note = Column(String)
    user = relationship("User", backref="orders")


db.Table('store',
         db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
         db.Column('product_id', db.Integer, db.ForeignKey('product.id')),
         )


class Wishlist(db.Model):
    __tablename__ = "wishlist"
    id = Column(Integer, primary_key=True)
    user = Column(Integer)
    product_id = Column(Integer, ForeignKey("product.id"))


def online_user():
    get_user = None
    if "username" in session:
        user = User.query.filter(User.email == session["username"]).first()
        get_user = user
    return get_user


def image_def(photo):
    photo_url = ""
    if photo:
        photo_file = secure_filename(photo.filename)
        photo_url = '/' + 'static/user_images/' + photo_file
        app.config['UPLOAD_FOLDER'] = 'static/user_images'
        photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_file))
    return photo_url


@app.route('/')
def main():  # put application's code here
    user = online_user()
    wishlist_check = Wishlist.query.filter(User.id == Wishlist.user).all()
    products = Product.query.all()
    date = Product.query.order_by(Product.date.desc()).all()
    return render_template("index.html", user=user, wishlist=wishlist_check, date=date, products=products)


@app.route('/cart')
def cart():
    user = online_user()
    if not user:
        return redirect(url_for("account"))
    else:
        data_check = Checkout.query.filter(Checkout.user_id == user.id).first()
        cart = User.query.filter(User.id == user.id).first()
        check = cart.product
        return render_template("cart.html", user=user, cart=cart, check=check, data_check=data_check)


@app.route('/add_cart/<int:product_id>')
def add_cart(product_id):
    user = online_user()
    if not user:
        return redirect(url_for("account"))
    else:
        buyer = User.query.filter(User.id == user.id).first()
        product = Product.query.filter(Product.id == product_id).first()
        if product not in buyer.product:
            buyer.product.append(product)
            db.session.commit()
        return redirect(url_for("cart", user=user))


@app.route('/delete_cart/<int:store_id>')
def delete_cart(store_id):
    user = online_user()
    product = Product.query.filter(Product.id == store_id).first()
    if product in user.product:
        user.product.remove(product)
        db.session.commit()
    return redirect(url_for("cart"))


@app.route('/blog')
def blog():
    user = online_user()
    return render_template("blog.html", user=user)


@app.route('/checkout', methods=["POST", "GET"])
def checkout():
    user = online_user()
    count = CountryInfo().all().keys()
    countries = sorted(count)
    if request.method == "POST":
        surname = request.form.get('surname')
        company = request.form.get('company')
        country = request.form.get('country')
        address_1 = request.form.get('address_1')
        address_2 = request.form.get('address_2')
        town = request.form.get('town')
        state = request.form.get('state')
        phone = request.form.get('phone')
        zip_code = request.form.get('zip')
        add = Checkout(
            user_id=user.id,
            surname=surname,
            company_name=company,
            country=country,
            street_address_1=address_1,
            street_address_2=address_2,
            town=town,
            state=state,
            zip_code=zip_code,
            number=phone
        )
        db.session.add(add)
        db.session.commit()
        return redirect(url_for("order_page", user=user))
    return render_template("checkout.html", countries=countries, user=user)


@app.route('/order_page', methods=["POST", "GET"])
def order_page():
    user = online_user()
    product_prices = []
    for prices in user.product:
        product_prices.append(prices.price)
    total = sum(product_prices)
    subtotal = total + (total * 0.1)
    if request.method == "POST":
        if user.product:
            note = request.form.get("information")
            products = []
            for item in user.product:
                products.append(item.id)
            new_order = Order(
                user_id=user.id,
                product_id=products,
                note=note,
                date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
            db.session.add(new_order)
            db.session.commit()
            user.product.clear()
            db.session.commit()
        return redirect(url_for("account_info"))
    return render_template("order.html", user=user, total=subtotal)


@app.route('/contact')
def contact():
    user = online_user()
    return render_template("contact.html", user=user)


@app.route('/faqs')
def faqs():
    user = online_user()
    return render_template("faqs.html", user=user)


@app.route('/shop', methods=["POST", "GET"])
def shop():
    user = online_user()
    if not user:
        return redirect(url_for("account"))
    else:
        wishlists = Wishlist.query.filter_by(user=user.id).all()
        query = Product.query
        if request.method == "POST":
            price = request.form.get("price_filter")
            brand = request.form.get("brand")
            category = request.form.get("category")
            if price and price != "all":
                if price == "f1":
                    query = query.filter(Product.price <= 100.0)
                if price == "f2":
                    query = query.filter(Product.price.between(101, 200))
                if price == "f3":
                    query = query.filter(Product.price.between(201, 300))
                if price == "f4":
                    query = query.filter(Product.price.between(301, 400))
                if price == "f5":
                    query = query.filter(Product.price.between(401, 500))
            if category and category != "all":
                query = query.filter(Product.category == category)
            if brand and brand != "all":
                query = query.filter(Product.brand == brand)
        wishlist_product_ids = []
        for item in wishlists:
            wishlist_product_ids.append(item.product_id)
        products = query.all()
        return render_template("shop.html", user=user, products=products, wishlist_product_ids=wishlist_product_ids)


@app.route('/single_post')
def single_post():
    user = online_user()
    return render_template("single-post.html", user=user)


@app.route('/single_product/<int:product_id>')
def single_product(product_id):
    user = online_user()
    if not user:
        return redirect(url_for("account"))
    else:
        product = Product.query.filter(Product.id == product_id).first()
        wishlist_item = Wishlist.query.filter_by(user=user.id, product_id=product.id).first()
        return render_template("single-product.html", user=user, product=product, wishlist_item=wishlist_item)


@app.route('/wishlist')
def wishlist():
    user = online_user()
    if not user:
        return redirect(url_for("account"))
    else:
        wishlists = Wishlist.query.filter(Wishlist.user == user.id).all()
        return render_template("wishlist.html", user=user, wishlists=wishlists)


@app.route('/wishlist_product/<int:product>')
def wishlist_product(product):
    user = online_user()
    if not user:
        return redirect(url_for("account"))
    else:
        add = Wishlist(
            user=user.id,
            product_id=product
        )
        db.session.add(add)
        db.session.commit()
        return redirect(url_for("shop"))


@app.route('/wishlist_delete/<int:product_id>')
def wishlist_delete(product_id):
    user = online_user()
    rem = Wishlist.query.filter(Wishlist.product_id == product_id).first()
    if user.id == rem.user:
        db.session.delete(rem)
        db.session.commit()
    return redirect(url_for("shop"))


@app.route('/product', methods=["POST", "GET"])
def product():
    user = online_user()
    products = Product.query.filter(Product.user_id == user.id).all()
    orders = Order.query.all()
    sold_dict = {}
    for product in products:
        count = 0
        for order in orders:
            if order.product_id == product.id:
                count += 1
        sold_dict[product.id] = count
    if request.method == "POST":
        name = request.form.get("name")
        brand = request.form.get("brand")
        price = request.form.get("price")
        description = request.form.get("description")
        category = request.form.get("category")
        image = request.files['image']
        back_image = request.files["back_image"]
        just_image = request.files["just_image"]
        side_image = request.files["side_image"]
        bottom_image = request.files["bottom_image"]
        colors = request.form.getlist('colors')
        front = image_def(image)
        back = image_def(back_image)
        just = image_def(just_image)
        side = image_def(side_image)
        bottom = image_def(bottom_image)
        date = datetime.now()
        add = Product(
            name=name,
            brand=brand,
            user_id=user.id,
            price=price,
            description=description,
            colors=colors,
            images=front,
            back_image=back,
            just_image=just,
            side_image=side,
            bottom_image=bottom,
            category=category,
            date=date
        )
        db.session.add(add)
        db.session.commit()
        return redirect(url_for("product"))
    return render_template("product_form.html", user=user, products=products, sold=sold_dict)


@app.route('/product_edit/<int:product_id>', methods=["POST", "GET"])
def product_edit(product_id):
    user = online_user()
    product = Product.query.filter(Product.id == product_id).first()
    if request.method == "POST":
        name = request.form.get("name")
        price = request.form.get("price")
        description = request.form.get("description")
        image = request.files['image']
        back_image = request.files["back_image"]
        just_image = request.files["just_image"]
        side_image = request.files["side_image"]
        bottom_image = request.files["bottom_image"]
        colors = request.form.getlist('colors')
        front = image_def(image)
        back = image_def(back_image)
        just = image_def(just_image)
        side = image_def(side_image)
        bottom = image_def(bottom_image)
        update_data = {
            "name": name,
            "price": price,
            "description": description,
            "colors": colors,
        }
        if image:
            update_data["images"] = front
        if back_image:
            update_data["back_image"] = back
        if just_image:
            update_data["just_image"] = just
        if side_image:
            update_data["side_image"] = side
        if bottom_image:
            update_data["bottom_image"] = bottom
        Product.query.filter(Product.id == product_id).update(update_data)
        db.session.commit()
        return redirect(url_for("product"))
    return render_template("product_edit.html", user=user, product=product)


@app.route('/delete_product/<int:product_id>')
def delete_product(product_id):
    rem = Product.query.filter(Product.id == product_id).first()
    db.session.delete(rem)
    db.session.commit()
    return redirect(url_for("product"))


@app.route('/about')
def about():
    user = online_user()
    return render_template('about-us.html', user=user)


@app.route('/account')
def account():
    user = online_user()
    return render_template('account.html', user=user)


@app.route('/account_info')
def account_info():
    user = online_user()
    countries = sorted(CountryInfo().all().keys())
    data_check = Checkout.query.filter_by(user_id=user.id).first()
    all_orders = Order.query.filter_by(user_id=user.id).all()
    shits = defaultdict(list)
    for order in all_orders:
        for items in order.product_id:
            products = Product.query.filter(Product.id == items).all()
            for product in products:
                shits[order.id].append(product)
    print(shits)
    return render_template('account_info.html', user=user, data_check=data_check, countries=countries,
                           orders=all_orders, products=shits)


@app.route('/register', methods=["POST", "GET"])
def register():
    if request.method == "POST":
        name = request.form.get('name')
        email = request.form.get('email')
        surname = request.form.get('surname')
        password = request.form.get('password')
        password_check = request.form.get('check_password')
        if password == password_check:
            hashed = generate_password_hash(password=password)
            user = User(name=name, email=email, password=hashed, surname=surname)
            db.session.add(user)
            db.session.commit()
        else:
            return redirect('register')
    return redirect(url_for('account'))


@app.route('/change_password', methods=["POST", "GET"])
def change_password():
    user = online_user()
    if request.method == "POST":
        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")
        if check_password_hash(user.password, old_password):
            password = generate_password_hash(password=new_password)
            User.query.filter(User.password == user.password).update({
                "password": password
            })
            db.session.commit()
            return redirect(url_for("account_info"))
    return redirect(url_for("account_info"))


@app.route('/api/data', methods=["GET", "POST"])
def data_get():
    total = request.get_json()
    session['total'] = total.get("total")
    response = {"message": "qabul qilindi", "malumot": total}
    return jsonify(response), 200


@app.route('/change_user_info', methods=["POST", "GET"])
def change_user_info():
    user = online_user()
    if request.method == "POST":
        email = request.form.get("email")
        username = request.form.get("name")
        surname = request.form.get("surname")
        User.query.filter(User.email == user.email).update({
            "email": email,
            "name": username,
            "surname": surname,
        })
        db.session.commit()
        return redirect(url_for("change_user_info"))
    return redirect(url_for("account_info", user=user))


@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter(User.email == email).first()
        if user:
            if check_password_hash(user.password, password):
                session["username"] = email
                return redirect(url_for("account_info", user=user))
            else:
                return redirect(url_for("login"))
        return redirect(url_for("login", user=user))
    return render_template("account.html", user=online_user())


@app.route('/checkout_update', methods=["POST", "GET"])
def checkout_update():
    user = online_user()
    if request.method == "POST":
        company = request.form.get('company')
        country = request.form.get('country')
        address_1 = request.form.get('address_1')
        address_2 = request.form.get('address_2')
        town = request.form.get('town')
        state = request.form.get('state')
        phone = request.form.get('phone')
        zip_code = request.form.get('zip')
        Checkout.query.filter(Checkout.user_id == user.id).update({
            "company_name": company,
            "country": country,
            "street_address_1": address_1,
            "street_address_2": address_2,
            "town": town,
            "state": state,
            "zip_code": zip_code,
            "number": phone,
        })
        db.session.commit()
        return redirect(url_for("checkout_update"))
    return redirect(url_for("account_info"))


@app.route('/admin_request')
def admin_request():
    user = online_user()
    check = Request.query.filter(Request.user_id == user.id).first()
    if not check and user.role != "seller":
        add = Request(
            user_id=user.id
        )
        db.session.add(add)
        db.session.commit()
    return redirect(url_for("account_info", user=user))


@app.route('/admin')
def admin():
    user = online_user()
    requests = Request.query.all()
    return render_template("admin.html", user=user, requests=requests)


@app.route('/approve/<int:user_id>')
def approve(user_id):
    User.query.filter(User.id == user_id).update({
        "role": "seller"
    })
    rem = Request.query.filter(Request.user_id == user_id).first()
    db.session.delete(rem)
    db.session.commit()
    return redirect(url_for("admin"))


@app.route('/reject/<int:user_id>')
def reject(user_id):
    rem = Request.query.filter(Request.user_id == user_id).first()
    db.session.delete(rem)
    db.session.commit()
    return redirect(url_for("admin"))


@app.route('/logout')
def logout():
    session['username'] = None
    return redirect(url_for("account"))


if __name__ == '__main__':
    app.run()
