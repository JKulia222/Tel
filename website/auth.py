import re

from flask import Blueprint, render_template, request, flash, redirect, url_for
from . import db
from .models import User, Note
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import exc
from flask_login import login_manager, login_user, login_required, logout_user, current_user

email_pattern = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return redirect(url_for('views.home', show_login_form=True), code=307)

    email = request.form.get('email')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first()
    print(user.password, password)
    if user:
        if check_password_hash(user.password, password):
            flash('Вы успешно вошли на сайт.', category='success')
            login_user(user, remember=True)
        else:
            flash('Введён неверный пароль.', category='error')
    else:
        flash('Пользователя с таким e-mail не существует', category='error')

    return redirect(url_for('views.home'))


@auth.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash('Вы успешно деавторизовались.', category='success')
    return redirect(url_for('views.home'))


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return redirect(url_for('views.home', show_signup_form=False), code=307)

    email = request.form.get('email')
    first_name = request.form.get('firstname')
    last_name = request.form.get('lastname')
    password1 = request.form.get('password1')
    password2 = request.form.get('password2')

    everything_is_ok = True

    if email is None or not email:
        everything_is_ok = False
        flash('Вы не указали e-mail.', category='error')
    elif not email_pattern.search(email):
        everything_is_ok = False
        flash('E-mail указан в недопустимом формате.', category='error')

    if first_name is None or not first_name:
        everything_is_ok = False
        flash('Вы не указали своё имя.', category='error')
    else:
        for ch in first_name:
            if not ch.isalpha() and ch != ' ' and ch != '-':
                everything_is_ok = False
                flash('Введённое Вами имя содержит недопустимые символы.\
					Оно должно состоять только из букв, пробелов и дефисов.', category='error')
                break

    if last_name is not None and not last_name:
        for ch in last_name:
            if not ch.isalpha() and ch != ' ' and ch != '-':
                everything_is_ok = False
                flash('Введённая Вами фамилия содержит недопустимые символы.\
					Она должна состоять только из букв, пробелов и дефисов.', category='error')
                break

    if password1 is None or not password1:
        everything_is_ok = False
        flash('Вы не указали пароль.', category='error')
    elif len(password1) < 7:
        everything_is_ok = False
        flash('Вы указали слишком короткий пароль: он должен иметь длину не менее 7 символов.', category='error')

    if password2 is None or not password2:
        everything_is_ok = False
        flash('Подтвердите указанный Вами пароль: введите его ещё раз.')
    elif password2 != password1:
        everything_is_ok = False
        flash('Введённые Вами пароли не совпадают.', category='error')

    if everything_is_ok:
        new_user = User(
            email=email,
            first_name=first_name, last_name=last_name,
            password=generate_password_hash(password1, method='sha256')
        )
        try:
            db.session.add(new_user)
            db.session.flush()
        except exc.IntegrityError:
            db.session.rollback()
            flash('Пользователь с таким e-mail уже существует.', category='error')
        except exc.SQLAlchemyError as e:
            db.session.rollback()
            flash(f'Не удалось создать нового пользователя. Ошибка: {e}', category='error')
        else:
            db.session.commit()
            flash('Новый пользователь успешно создан.', category='success')
            login_user(new_user, remember=True)
            return redirect(url_for('views.home'))

    return redirect(url_for('views.home'))
