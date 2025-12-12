from flask import render_template, url_for, redirect, request
from flask_login import login_required, login_user, logout_user, current_user
from appfleshi.forms import LoginForm, RegisterForm, PhotoForm
from appfleshi import app, database, bcrypt
from appfleshi.models import User, Photo, Like
import os
from werkzeug.utils import secure_filename
import time

@app.route('/', methods=['GET', 'POST'])
def homepage():
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
    if int(user_id) != int(current_user.id):
        user = User.query.get(int(user_id))
        return render_template('profile.html', user=user, form=None)

    photo_form = PhotoForm()

    if photo_form.validate_on_submit():
        files = request.files.getlist("photo")

        for file in files:
            if file.filename == "":
                continue

            filename, ext = os.path.splitext(file.filename)
            unique_name = f"{filename}_{int(time.time())}{ext}"

            path = os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['UPLOAD_FOLDER'],secure_filename(unique_name))
            file.save(path)

            photo = Photo(file_name=unique_name, user_id=current_user.id)
            database.session.add(photo)

        database.session.commit()
        return redirect(url_for('profile', user_id=current_user.id))

    return render_template('profile.html', user=current_user, form=photo_form)

@app.route('/createaccount', methods=['GET', 'POST'])
def createaccount():
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
    photos = Photo.query.order_by(Photo.upload_date.desc()).all()
    return render_template("feed.html", photos=photos)

@app.route('/deletephoto/<photo_id>', methods=['GET', 'POST'])
@login_required
def delete_photo(photo_id):
    photo = Photo.query.get(photo_id)

    if photo.user_id != current_user.id:
        return "Acesso negado", 403

    path = os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['UPLOAD_FOLDER'], photo.file_name)
    if os.path.exists(path):
        os.remove(path)

        database.session.delete(photo)
        database.session.commit()

        return redirect(url_for('profile', user_id=photo.user_id))

@app.route('/like/<photo_id>', methods=['POST'])
@login_required
def like(photo_id):
    existing_like = Like.query.filter_by(user_id=current_user.id, photo_id=photo_id).first()

    if existing_like:
        database.session.delete(existing_like)
    else:
        like = Like(user_id=current_user.id, photo_id=photo_id)
        database.session.add(like)

    database.session.commit()
    return redirect(url_for('feed'))