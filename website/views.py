from flask import Blueprint, render_template, redirect, request, flash, url_for, jsonify
from . import db
from .models import Note
from sqlalchemy import desc
from flask_login import current_user
from werkzeug.security import generate_password_hash
from datetime import datetime

import json

views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
def home():
    notes = Note.query.order_by(desc(Note.creation_date)).all()

    show_login_form, show_signup_form = False, False

    if request.method == 'POST':
        if 'show_login_form' in request.form:
            show_login_form = request.form['show_login_form']
        if 'show_signup_form' in request.form:
            show_signup_form = request.form['show_signup_form']

    return render_template(
        "home.html", user=current_user, notes=notes,
        show_login_form=show_login_form, show_signup_form=show_signup_form
    )


@views.route('/my-notes')
def my_notes():
    if not current_user.is_authenticated:
        return "Чтобы просмотреть свои заметки, нужно вначале войти на сайт под своей учётной записью."

    notes = Note.query.filter_by(author_id=current_user.id).order_by(desc(Note.creation_date)).all()

    return render_template(
        "home.html", user=current_user, notes=notes,
        show_login_form=False, show_signup_form=False
    )


@views.route('/search')
def search():
    query = request.args.get('query')

    if not query:
        return redirect(url_for('views.home'))

    notes = Note.query.filter(Note.topic.contains(query) | Note.content.contains(query)) \
        .order_by(desc(Note.creation_date)).all()

    return render_template(
        "home.html", user=current_user, notes=notes,
        show_login_form=False, show_signup_form=False
    )


@views.route('/profile', methods=['GET', 'POST'])
def profile():
    if not current_user.is_authenticated:
        return 'Для того чтобы изменить сведения о пользователе, ' \
               'необходимо сначала войти на сайт под его учётной записью.'

    if request.method == 'GET':
        return render_template('profile.html', user=current_user)

    first_name = request.form.get('firstname')
    last_name = request.form.get('lastname')
    password1 = request.form.get('password1')
    password2 = request.form.get('password2')

    everything_is_ok = True

    if first_name is None or not first_name:
        first_name = current_user.first_name
    else:
        for ch in first_name:
            if not ch.isalpha() and ch != ' ' and ch != '-':
                everything_is_ok = False
                flash('Введённое Вами имя содержит недопустимые символы.\
					Оно должно состоять только из букв, пробелов и дефисов.', category='error')
                break

    if last_name is None:
        last_name = current_user.last_name
    else:
        for ch in last_name:
            if not ch.isalpha() and ch != ' ' and ch != '-':
                everything_is_ok = False
                flash('Введённая Вами фамилия содержит недопустимые символы.\
					Она должна состоять только из букв, пробелов и дефисов.', category='error')
                break

    if password1 != password2:
        everything_is_ok = False
        flash('Введённые Вами пароли не совпадают.', category='error')

    if not password1:
        password1 = None
    elif password1 is not None:
        if len(password1) < 7:
            everything_is_ok = False
            flash('Вы указали слишком короткий пароль: он должен иметь длину не менее 7 символов.', category='error')

    if everything_is_ok:
        current_user.first_name = first_name
        current_user.last_name = last_name
        if password1 is not None:
            current_user.password = generate_password_hash(password1)
        db.session.commit()
        return redirect(url_for('views.home'))
    else:
        return render_template('profile.html', user=current_user)


@views.route('/new-note', methods=['GET', 'POST'])
def new_note():
    if not current_user.is_authenticated:
        return 'Для того чтобы создавать заметки, необходимо вначале войти на сайт под своей учётной записью.'

    if request.method == 'GET':
        return render_template('new-note.html', user=current_user)

    topic = request.form.get('topic')
    content = request.form.get('content')
    is_public = request.form.get('ispublic')

    everything_is_ok = True

    if topic is None or not topic:
        everything_is_ok = False
        flash('Поле "Тема" не может быть пустым.', category='error')

    if content is None or not content:
        everything_is_ok = False
        flash('Содержание сообщения не может быть пустым', category='error')

    if is_public is None:
        is_public = False
    else:
        is_public = True

    if everything_is_ok:
        new_note = Note(topic=topic, content=content, author_id=current_user.id, is_public=is_public)
        try:
            db.session.add(new_note)
            db.session.flush()
        except:
            db.session.rollback()
            flash('Не удалось создать новую заметку.', category='error')
        else:
            db.session.commit()
            flash('Новая заметка успешно создана.', category='success')
        return redirect(url_for('views.home'))
    else:
        return render_template(
            'new-note.html',
            user=current_user, topic=topic, content=content, is_public=is_public
        )


@views.route('/notes/<int:note_id>')
def get_note(note_id):
    note = Note.query.get(note_id)

    if not note:
        return "Статьи с указанным номером не существует."

    if not current_user.is_authenticated and not note.is_public:
        return "Эта статья доступна только зарегистрированным пользователям."

    return render_template('note.html', user=current_user, note=note)


@views.route('/edit-note/<int:note_id>', methods=['GET', 'POST'])
def edit_note(note_id):
    note = Note.query.get(note_id)

    if not note:
        return "Статьи с указанным номером не существует."

    if not current_user.is_authenticated:
        return "Возможность редактирования есть только у зарегистрированных пользователей, " \
               "причём пользователи могут редактировать только свои собственные статьи."

    if note.author_id != current_user.id:
        return "Пользователи могут редактировать только свои собственные статьи."

    if request.method == 'GET':
        return render_template('edit-note.html', user=current_user, note=note)

    topic = request.form.get('topic')
    content = request.form.get('content')
    is_public = request.form.get('ispublic')

    everything_is_ok = True

    if topic is None or not topic:
        everything_is_ok = False
        flash('Поле "Тема" не может быть пустым.', category='error')

    if content is None or not content:
        everything_is_ok = False
        flash('Содержание сообщения не может быть пустым', category='error')

    if is_public is None:
        is_public = False
    else:
        is_public = True

    if everything_is_ok:
        try:
            note.topic = topic
            note.content = content
            note.is_public = is_public
            note.modification_date = datetime.utcnow()
            db.session.flush()
        except:
            db.session.rollback()
            flash('Не удалось изменить заметку.', category='error')
        else:
            db.session.commit()
            flash('Изменения успешно сохранены.', category='success')
        return redirect(url_for('views.home'))
    else:
        return render_template('edit-note.html', user=current_user, note=note)


@views.route('/delete-note/<int:note_id>')
def delete_note(note_id):
    note = Note.query.get(note_id)

    if not note:
        return "Статьи с указанным номером не существует."

    if not current_user.is_authenticated:
        return "Возможность удаления есть только у зарегистрированных пользователей, " \
               "причём пользователи могут удалять только свои собственные статьи."

    if note.author_id != current_user.id:
        return "Пользователи могут удалять только свои собственные статьи."

    try:
        db.session.delete(note)
        db.session.flush()
    except:
        db.session.rollback()
        flash('Не удалось удалить заметку.', category='error')
    else:
        db.session.commit()
        flash('Заметка успешно удалена.', category='success')

    return redirect(url_for('views.home'))
