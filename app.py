from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from config import Config
from models import db, Product, Category, Subcategory, Customer, Order, OrderItem, Admin
from admin_crud import admin_bp
import pandas as pd
from io import BytesIO
from flask import jsonify, flash, render_template, flash, redirect, url_for, abort
from utils import generate_order_pdf

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
app.register_blueprint(admin_bp)



# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(admin_id):
    return Admin.query.get(int(admin_id))

# Головна сторінка
@app.route("/")
def index():
    q = request.args.get("q")
    category_id = request.args.get("category")
    subcategory_id = request.args.get("subcategory")

    query = Product.query.join(Subcategory)

    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))

    if category_id:
        query = query.filter(Subcategory.category_id == category_id)

    if subcategory_id:
        query = query.filter(Product.subcategory_id == subcategory_id)

    products = query.all()
    categories = Category.query.all()
    subcategories = Subcategory.query.all()

    return render_template(
        "index.html",
        products=products,
        categories=categories,
        subcategories=subcategories
    )


# Сторінка замовлення
@app.route("/product/<int:product_id>", methods=["GET", "POST"])
def product_page(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        quantity = int(request.form["quantity"])
        email = request.form["email"]
        address = request.form["address"]

        customer = Customer.query.filter_by(name=name, phone=phone).first()
        if not customer:
            customer = Customer(name=name, phone=phone, email=email, address=address)
            db.session.add(customer)
            db.session.commit()

        order = Order(customer_id=customer.id)
        db.session.add(order)
        db.session.commit()

        item = OrderItem(order_id=order.id, product_id=product.id, quantity=quantity, unit_price=product.price)
        db.session.add(item)
        order.total = quantity * product.price
        db.session.commit()

        # після збереження замовлення в БД
        return redirect(url_for('order_summary', order_id=order.id))
    return render_template("product.html", product=product)

@app.route("/order/<int:order_id>/summary")
def order_summary(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template("order_summary.html", order=order)

# Перегляд замовлень
@app.route("/orders")
def orders():
    status = request.args.get("status")
    query = Order.query.order_by(Order.date.desc())

    if status:
        query = query.filter(Order.status == status)

    all_orders = query.all()
    return render_template("orders.html", orders=all_orders)



# Експорт у Excel
@app.route("/export_orders")
def export_orders():
    orders = Order.query.all()
    rows = []
    for order in orders:
        for item in order.items:
            rows.append({
                "Клієнт": order.customer.name,
                "Телефон": order.customer.phone,
                "Дата": order.date.strftime("%Y-%m-%d %H:%M"),
                "Товар": item.product.name,
                "Кількість": item.quantity,
                "Ціна за одиницю": item.unit_price,
                "Сума": item.quantity * item.unit_price,
                "Статус": order.status
            })
    df = pd.DataFrame(rows)
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    return send_file(output, download_name="orders_export.xlsx", as_attachment=True)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        print("🟡 Введено:", username, password)

        admin = Admin.query.filter_by(username=username).first()
        print("🟢 Знайдено:", admin.username if admin else None, admin.password if admin else None)

        if admin and admin.password == password:
            print("✅ Пароль збігся — входимо")
            login_user(admin, remember=True)
            print("🔒 Поточний користувач:", current_user.is_authenticated, current_user.username)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("admin_bp.admin_dashboard"))
        
        print("❌ Невірний логін або пароль")
        flash("Невірний логін або пароль", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/check_session")
@login_required
def check_session():
    return f"👤 Ви увійшли як: {current_user.username}"

@app.route("/orders/mark/<int:order_id>/<status>")
def mark_order(order_id, status):
    order = Order.query.get_or_404(order_id)

    if order.status != "нове":
        flash(f"⚠️ Замовлення #{order.id} вже має статус: {order.status}", "warning")
        return redirect(url_for("orders"))

    if status not in ["опрацьовано", "відмова"]:
        abort(400)

    order.status = status
    db.session.commit()
    flash(f"📝 Статус замовлення #{order.id} змінено на: {status}", "info")
    return redirect(url_for("orders"))

@app.route("/order/<int:order_id>/preview")
def preview_order_pdf(order_id):
    order = Order.query.get_or_404(order_id)
    pdf = generate_order_pdf(order)
    return send_file(pdf, mimetype="application/pdf")

@app.route("/order/<int:order_id>/pdf")
def download_order_pdf(order_id):
    order = Order.query.get_or_404(order_id)
    pdf = generate_order_pdf(order)
    return send_file(pdf, as_attachment=True, download_name=f"order_{order.id}.pdf", mimetype="application/pdf")

with app.app_context():
    db.create_all()
    
    if not Admin.query.first():
        admin = Admin(username="admin", password="admin123")
        db.session.add(admin)
        db.session.commit()
        print("✅ Створено адміністратора: admin/admin123")

    
    if not Category.query.first():
        categories_with_subs = {
            "Компʼютери та ноутбуки": ["Ноутбуки", "Системні блоки", "Моноблоки", "Нетбуки"],
            "Периферія": ["Миші", "Клавіатури", "Комплекти", "Килимки", "Геймпади", "Веб-камери", "Гарнітури"],
            "Накопичувачі": ["Флешки", "HDD", "SSD", "Карти памʼяті", "DVD-диски"],
            "Мережеве обладнання": ["Wi-Fi роутери", "Комутатори", "Карти", "Кабелі", "Bluetooth"],
            "Друк і сканування": ["Принтери", "МФУ", "Сканери", "Ламіна́тори", "Шредери"],
            "Офісні меблі": ["Крісла", "Стійки", "Кріплення", "Засоби для чищення"],
            "Аксесуари": ["Сумки", "Охолоджувачі", "Хаби", "Адаптери", "Блоки живлення", "Акумулятори"],
            "ПЗ": ["ОС", "Офісні пакети", "Антивіруси", "ПЗ для бухгалтерії", "Навчальні"],
            "Інше": ["Подовжувачі", "Захисні екрани", "Інше обладнання"]
        }

        for cat_name, sub_list in categories_with_subs.items():
            cat = Category(name=cat_name)
            db.session.add(cat)
            db.session.flush()

            for sub in sub_list:
                db.session.add(Subcategory(name=sub, category_id=cat.id))

        db.session.commit()
        print("✅ Категорії та підкатегорії додано.")

    if not Product.query.first():
        demo_products = {
            "Ноутбуки": [
                ("Lenovo IdeaPad 3", 23500, 10, "lenovo.png"),
                ("HP Pavilion", 27500, 5, "hp.png")
            ],
            "Миші": [
                ("Logitech M185", 550, 30, "logitech.png")
            ]
        }

        subcategories = Subcategory.query.all()
        for sub in subcategories:
            if sub.name in demo_products:
                for name, price, stock, img in demo_products[sub.name]:
                    db.session.add(Product(
                        name=name,
                        price=price,
                        stock=stock,
                        description=f"Товар з підкатегорії {sub.name}",
                        image_url=img,
                        subcategory_id=sub.id
                    ))
        db.session.commit()
        print("✅ Товари додано.")

@app.route("/get_subcategories/<int:category_id>")
def get_subcategories(category_id):
    subcategories = Subcategory.query.filter_by(category_id=category_id).all()
    data = [{"id": sub.id, "name": sub.name} for sub in subcategories]
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)

