from flask import Blueprint, render_template, jsonify, url_for, flash, redirect, request, abort
from flask_login import login_user, current_user, logout_user, login_required
from app.forms import RegistrationForm, LoginForm, GroceryListForm, GroceryListItemForm
from app.models import User, Product, GroceryList, GroceryListItem
from app import db, bcrypt
from collections import defaultdict
from app.utils import find_similar_products
import json

main = Blueprint('main', __name__)


@main.route('/')
@main.route('/home')
def home():
    return render_template('products.html', products=Product.query.all())


@main.route('/api/products')
def api_products():
    with open('products.json') as file:
        products = json.load(file)
    return jsonify(products)


@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        user = User(username=form.username.data,
                    email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)


@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@main.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.home'))


@main.route('/account')
@login_required
def account():
    return render_template('account.html', title='Account')


@main.route('/grocery_lists', methods=['GET', 'POST'])
@login_required
def grocery_lists():
    form = GroceryListForm()
    if form.validate_on_submit():
        grocery_list = GroceryList(name=form.name.data, user=current_user)
        db.session.add(grocery_list)
        db.session.commit()
        flash('Grocery list created!', 'success')
        return redirect(url_for('main.grocery_lists'))
    grocery_lists = GroceryList.query.filter_by(user=current_user).all()
    return render_template('grocery_lists.html', title='Grocery Lists', form=form, grocery_lists=grocery_lists)


@main.route('/grocery_list/<int:grocery_list_id>', methods=['GET', 'POST'])
@login_required
def grocery_list(grocery_list_id):
    grocery_list = GroceryList.query.get_or_404(grocery_list_id)
    if grocery_list.user != current_user:
        abort(403)
    form = GroceryListItemForm()
    if form.validate_on_submit():
        products = Product.query.all()
        similar_products = find_similar_products(
            form.product_name.data, products)
        if not similar_products:
            flash('No similar products found', 'danger')
            return redirect(url_for('main.grocery_list', grocery_list_id=grocery_list.id))
        product = similar_products[0]
        item = GroceryListItem(quantity=form.quantity.data,
                               grocery_list=grocery_list, product=product)
        db.session.add(item)
        db.session.commit()
        flash('Item added to list!', 'success')
        return redirect(url_for('main.grocery_list', grocery_list_id=grocery_list.id))
    items = GroceryListItem.query.filter_by(grocery_list=grocery_list).all()
    return render_template('grocery_list.html', title=grocery_list.name, form=form, items=items, grocery_list=grocery_list)


@main.route('/grocery_list/<int:grocery_list_id>/update', methods=['GET', 'POST'])
@login_required
def update_grocery_list(grocery_list_id):
    grocery_list = GroceryList.query.get_or_404(grocery_list_id)
    if grocery_list.user != current_user:
        abort(403)
    form = GroceryListForm()
    if form.validate_on_submit():
        grocery_list.name = form.name.data
        db.session.commit()
        flash('Your grocery list has been updated!', 'success')
        return redirect(url_for('main.grocery_list', grocery_list_id=grocery_list.id))
    elif request.method == 'GET':
        form.name.data = grocery_list.name
    return render_template('create_grocery_list.html', title='Update Grocery List', form=form, legend='Update Grocery List')


@main.route('/grocery_list/<int:grocery_list_id>/delete', methods=['POST'])
@login_required
def delete_grocery_list(grocery_list_id):
    grocery_list = GroceryList.query.get_or_404(grocery_list_id)
    if grocery_list.user != current_user:
        abort(403)
    for item in grocery_list.items:
        db.session.delete(item)
    db.session.delete(grocery_list)
    db.session.commit()
    flash('Your grocery list has been deleted!', 'success')
    return redirect(url_for('main.grocery_lists'))


@main.route('/grocery_list_item/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_grocery_list_item(item_id):
    item = GroceryListItem.query.get_or_404(item_id)
    grocery_list_id = item.grocery_list_id
    if item.grocery_list.user != current_user:
        abort(403)
    db.session.delete(item)
    db.session.commit()
    flash('The item has been deleted from your list!', 'success')
    return redirect(url_for('main.grocery_list', grocery_list_id=grocery_list_id))


@main.route('/categorized_products')
def categorized_products():
    products = Product.query.all()
    categorized = defaultdict(list)
    default_logo_url = url_for('static', filename='default_store_logo.png')
    for product in products:
        categorized[product.store_name].append(product)
    return render_template('categorized_products.html', title='Categorized Products', categorized=categorized, default_logo_url=default_logo_url)


@main.route('/store/<store_name>')
def store_products(store_name):
    products = Product.query.filter_by(store_name=store_name).all()
    return render_template('store_products.html', title=f'{store_name} Products', products=products, store_name=store_name)
