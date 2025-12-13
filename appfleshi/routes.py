from flask import render_template, url_for, redirect
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

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('profile', user_id=user.id))

    return render_template('homepage.html', form=form)

@app.route('/profile/<user_id>', methods=['GET', 'POST'])
@login_required
def profile(user_id):
    user = User.query.get_or_404(int(user_id))

    photo_form = PhotoForm()

    if photo_form.validate_on_submit():
        file = photo_form.photo.data

        if file:
            filename = secure_filename(file.filename)
            unique_name = f"{int(time.time())}_{filename}"

            path = os.path.join(app.root_path,app.config['UPLOAD_FOLDER'],unique_name)

            file.save(path)

            photo = Photo(file_name=unique_name,user_id=current_user.id)

            database.session.add(photo)
            database.session.commit()

            return redirect(url_for('profile', user_id=current_user.id))

    return render_template(
        'profile.html',user=user,photo_form=photo_form)

@app.route('/createaccount', methods=['GET', 'POST'])
def createaccount():
    if current_user.is_authenticated:
        return redirect(url_for('profile', user_id=current_user.id))

    form = RegisterForm()

    if form.validate_on_submit():
        password = bcrypt.generate_password_hash(form.password.data)
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=password
        )

        database.session.add(user)
        database.session.commit()

        return redirect(url_for('homepage'))

    return render_template('createaccount.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('homepage'))

@app.route('/feed')
@login_required
def feed():
    photos = Photo.query.order_by(Photo.timestamp.desc()).all()

    photo_likes = {photo.id: Like.query.filter_by(photo_id=photo.id).count()for photo in photos}

    liked_photos = {like.photo_id for like in Like.query.filter_by(user_id=current_user.id).all()}

    form = CommentForm()

    return render_template('feed.html',photos=photos,photo_likes=photo_likes,liked_photos=liked_photos,form=form)

@app.route('/deletephoto/<photo_id>', methods=['POST'])
@login_required
def delete_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)

    if photo.user_id != current_user.id:
        return "Acesso negado", 403

    Like.query.filter_by(photo_id=photo.id).delete()
    Comment.query.filter_by(photo_id=photo.id).delete()

    path = os.path.join(app.root_path,app.config['UPLOAD_FOLDER'], photo.file_name)

    if os.path.exists(path):
        os.remove(path)

    database.session.delete(photo)
    database.session.commit()

    return redirect(url_for('profile', user_id=current_user.id))

@app.route('/like/<photo_id>', methods=['POST'])
@login_required
def like(photo_id):
    photo = Photo.query.get_or_404(photo_id)

    like = Like.query.filter_by(user_id=current_user.id,photo_id=photo.id).first()

    if like:
        database.session.delete(like)
    else:
        database.session.add(Like(user_id=current_user.id, photo_id=photo.id))

    database.session.commit()
    return redirect(url_for('feed'))

@app.route('/comment/<photo_id>', methods=['POST'])
@login_required
def comment(photo_id):
    form = CommentForm()

    if form.validate_on_submit():
        comment = Comment(content=form.content.data, user_id=current_user.id,photo_id=photo_id)

        database.session.add(comment)
        database.session.commit()

    return redirect(url_for('feed'))