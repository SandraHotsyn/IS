# admin_crud.py (фрагмент для вбудови в app.py або окремий blueprint)
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user, logout_user
from models import Product, Subcategory, db,  Category

from forms import ProductForm
import os  # 📁 для збереження файлу у папку
from werkzeug.utils import secure_filename

admin_bp = Blueprint("admin_bp", __name__)
UPLOAD_FOLDER = "static/images"

# --- Вивід списку товарів ---

@admin_bp.route("/admin/products")
@login_required
def admin_products():
    search = request.args.get("q", "").strip()
    query = Product.query

    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    products = query.all()
    return render_template("admin_products.html", products=products, title="Управління товарами")


# --- Створення товару ---
@admin_bp.route("/admin/products/create", methods=["GET", "POST"])
@login_required
def create_product():
    form = ProductForm()
    form.subcategory_id.choices = [(s.id, f"{s.name} ({s.category.name})") for s in Subcategory.query.all()]

    if form.validate_on_submit():
        # 🖼️ Обробка зображення
        filename = None
        if form.image.data:  # ✅ Перевіряємо, чи файл було вибрано
            filename = secure_filename(form.image.data.filename)
            form.image.data.save(os.path.join(UPLOAD_FOLDER, filename))

        # 📦 Створюємо об'єкт товару
        product = Product(
            name=form.name.data,
            price=form.price.data,
            stock=form.stock.data,
            description=form.description.data,
            image_url=filename,  # ✅ Записуємо ім’я файлу
            subcategory_id=form.subcategory_id.data
        )
        db.session.add(product)
        db.session.commit()
        flash("✅ Товар успішно додано", "success")
        return redirect(url_for("admin_bp.admin_products"))

    return render_template("admin_product_form.html", form=form, title="Додати товар")

# --- Редагування товару ---
@admin_bp.route("/admin/products/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    form.subcategory_id.choices = [(s.id, f"{s.name} ({s.category.name})") for s in Subcategory.query.all()]

    if form.validate_on_submit():
        form.populate_obj(product)  # 📋 Заповнює всі звичайні поля (крім файлу)

        # 🖼️ Якщо вибрано новий файл — оновлюємо зображення
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            form.image.data.save(os.path.join(UPLOAD_FOLDER, filename))
            product.image_url = filename  # ✅ Оновлюємо посилання в базі

        db.session.commit()
        flash("✏️ Зміни збережено", "info")
        return redirect(url_for("admin_bp.admin_products"))

    return render_template("admin_product_form.html", form=form, product=product, title="Редагувати товар")


# --- Видалення товару ---
@admin_bp.route("/admin/products/<int:product_id>/delete", methods=["POST"])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash("🗑️ Товар видалено", "warning")
    return redirect(url_for("admin_bp.admin_products"))

# --- Панель керування ---
@admin_bp.route("/admin")
@login_required
def admin_dashboard():
    return render_template("admin_dashboard.html", title="Адмін-панель")

@admin_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@admin_bp.route("/admin/categories", methods=["GET", "POST"])
@login_required
def admin_categories():
    if request.method == "POST":
        name = request.form["name"].strip()
        if name:
            new_cat = Category(name=name)
            db.session.add(new_cat)
            db.session.commit()
            flash("✅ Категорію додано", "success")
    categories = Category.query.all()
    return render_template("admin_categories.html", categories=categories)

@admin_bp.route("/admin/subcategories", methods=["GET", "POST"])
@login_required
def admin_subcategories():
    categories = Category.query.all()
    if request.method == "POST":
        name = request.form["name"].strip()
        category_id = request.form["category_id"]
        if name and category_id:
            new_sub = Subcategory(name=name, category_id=int(category_id))
            db.session.add(new_sub)
            db.session.commit()
            flash("✅ Підкатегорію додано", "success")
    subcategories = Subcategory.query.all()
    return render_template("admin_subcategories.html", subcategories=subcategories, categories=categories)

@admin_bp.route("/admin/categories/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_category(id):
    category = Category.query.get_or_404(id)
    if request.method == "POST":
        category.name = request.form["name"]
        db.session.commit()
        flash("✅ Категорію оновлено", "success")
        return redirect(url_for("admin_bp.admin_categories"))
    return render_template("admin_edit_category.html", category=category)

@admin_bp.route("/admin/categories/delete/<int:id>")
@login_required
def delete_category(id):
    category = Category.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    flash("🗑 Категорію видалено", "info")
    return redirect(url_for("admin_bp.admin_categories"))

@admin_bp.route("/admin/subcategories/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_subcategory(id):
    sub = Subcategory.query.get_or_404(id)
    categories = Category.query.all()

    if request.method == "POST":
        sub.name = request.form["name"]
        sub.category_id = request.form["category_id"]
        db.session.commit()
        flash("✅ Підкатегорію оновлено", "success")
        return redirect(url_for("admin_bp.admin_subcategories"))

    return render_template("admin_edit_subcategory.html", sub=sub, categories=categories)

@admin_bp.route("/admin/subcategories/delete/<int:id>")
@login_required
def delete_subcategory(id):
    sub = Subcategory.query.get_or_404(id)
    db.session.delete(sub)
    db.session.commit()
    flash("🗑 Підкатегорію видалено", "info")
    return redirect(url_for("admin_bp.admin_subcategories"))
