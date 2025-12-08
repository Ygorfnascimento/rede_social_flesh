from flask import render_template, url_for, redirect
from flask_login import login_required, login_user, logout_user, current_user
from appfleshi.forms import LoginForm, RegisterForm, PhotoForm
from appfleshi import app, database, bcrypt
from appfleshi.models import User, Photo
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
    if int(user_id) == int(current_user.id):
        photo_form = PhotoForm()
        if photo_form.validate_on_submit():
            file = photo_form.photo.data

            filename, ext = os.path.splitext(file.filename)
            unique_name = f"{filename}_{int(time.time())}{ext}"

            path = os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'], unique_name)
            file.save(path)

            existing_photo = Photo.query.filter_by(user_id=current_user.id).first()
            if existing_photo:
                old_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'],
                                        existing_photo.file_name)
                if os.path.exists(old_path):
                    os.remove(old_path)
                existing_photo.file_name = unique_name
            else:
                photo = Photo(file_name=unique_name, user_id=current_user.id)
                database.session.add(photo)

            database.session.commit()

        return render_template('profile.html', user=current_user, form=photo_form)
    else:
        user = User.query.get(int(user_id))
        return render_template('profile.html', user=user, form=None)


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