from flask import render_template, url_for, redirect, request
from flask_login import login_required, login_user, logout_user, current_user
from appfleshi.forms import LoginForm, RegisterForm, PhotoForm, CommentForm
from appfleshi import app, database, bcrypt
from appfleshi.models import User, Photo, Like, Comment
import os
from werkzeug.utils import secure_filename
import time

@app.route('/', methods=['GET', 'POST'])
def homepage():

    if current_user.is_authenticated:
        return redirect(url_for('profile', user_id=current_user.id))

    login_form = LoginForm()

    if login_form.validate_on_submit():
        user = User.query.filter_by(email=login_form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, login_form.password.data):
            login_user(user)
            return redirect(url_for('profile', user_id=user.id))

    return render_template('homepage.html', form=login_form)

@app.route('/profile/<user_id>', methods=['GET', 'POST'])
@login_required
def profile(user_id):
    user = User.query.get(int(user_id))

    # Se o usuário não for encontrado, retornar um erro 404
    if user is None:
        return "Usuário não encontrado", 404

    if int(user_id) != int(current_user.id):
        return render_template('profile.html', user=user, form=None)

    comment_form = CommentForm()  # Formulário para comentar nas fotos
    photo_form = PhotoForm()  # Formulário para upload de fotos

    if comment_form.validate_on_submit():
        content = comment_form.content.data
        photo_id = request.form.get('photo_id')
        new_comment = Comment(content=content, user_id=current_user.id, photo_id=photo_id)
        database.session.add(new_comment)
        database.session.commit()
        return redirect(url_for('profile', user_id=current_user.id))

    return render_template('profile.html', user=user, comment_form=comment_form, photo_form=photo_form)


@app.route('/createaccount', methods=['GET', 'POST'])
def createaccount():
    if current_user.is_authenticated:
        return redirect(url_for('profile', user_id=current_user.id))

    register_form = RegisterForm()

    if register_form.validate_on_submit():
        password = bcrypt.generate_password_hash(register_form.password.data)
        user = User(username=register_form.username.data, password=password, email=register_form.email.data)
        database.session.add(user)
        database.session.commit()
        login_user(user, remember=True)

        return redirect(url_for('profile', user_id=user.id))

    return render_template('createaccount.html', form=register_form)


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('homepage'))

@app.route("/feed")
@login_required
def feed():
    photos = Photo.query.order_by(Photo.timestamp.desc()).all()

    photo_likes = {}

    for photo in photos:
        photo_likes[photo.id] = Like.query.filter_by(photo_id=photo.id).count()

    form = CommentForm()

    return render_template("feed.html", photos=photos, photo_likes=photo_likes, form=form)

@app.route('/deletephoto/<photo_id>', methods=['POST'])
@login_required
def delete_photo(photo_id):
    photo = Photo.query.get(photo_id)

    # Verifica se o usuário é o proprietário da foto
    if photo.user_id != current_user.id:
        return "Acesso negado", 403

    # Exclui o arquivo de foto do sistema de arquivos
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'], photo.file_name)
    if os.path.exists(path):
        os.remove(path)

    # Exclui a foto do banco de dados
    database.session.delete(photo)
    database.session.commit()

    return redirect(url_for('profile', user_id=current_user.id))

@app.route('/like/<photo_id>', methods=['POST'])
@login_required
def like(photo_id):
    photo = Photo.query.get_or_404(photo_id)

    existing_like = Like.query.filter_by(user_id=current_user.id, photo_id=photo.id).first()

    if existing_like:
        database.session.delete(existing_like)
    else:
        new_like = Like(user_id=current_user.id, photo_id=photo.id)
        database.session.add(new_like)

    database.session.commit()

    return redirect(url_for('feed'))

@app.route('/comment/<photo_id>', methods=['POST'])
@login_required
def comment(photo_id):
    form = CommentForm()
    if form.validate_on_submit():
        content = form.content.data
        new_comment = Comment(content=content, user_id=current_user.id, photo_id=photo_id)
        database.session.add(new_comment)
        database.session.commit()
        return redirect(url_for('feed'))
    return redirect(url_for('feed'))