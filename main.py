import os
from flask import Flask, render_template
from flask import redirect, request
from data import db_session
from data import posts_resources
from data.users import User
from data.posts import Posts
from forms.user import RegisterForm
from flask_login import LoginManager
from forms.user import LoginForm
from forms.posts import PostsForm
from flask_login import login_user, login_required, logout_user, current_user
from flask_restful import abort, Api

from waitress import serve

app = Flask(__name__)
file_path = os.path.abspath(os.getcwd()) + "/db/guestbook.db"
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+ file_path
login_manager = LoginManager()
login_manager.init_app(app)

# создаём API

api = Api(app, catch_all_404s=True)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')
@app.route('/home')
def index():
    return render_template("index.html", title="Багровый фантомас, ю ноу блин", home="active")


@app.route('/media')
def about():
    return render_template("media.html", media="active", title="Наши величайшие в истории медиа")


@app.route('/guestbook')
def guestbook():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        posts = db_sess.query(Posts).filter(
            (Posts.user == current_user) | (Posts.is_private != True))
    else:
        posts = db_sess.query(Posts).filter(Posts.is_private != True)
    return render_template("guestbook.html", gbook="active", posts=posts, title="Книжечка гостевая")


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title="Регистрация", reg="active", form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Вход', log="active", form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/post', methods=['GET', 'POST'])
@login_required
def add_posts():
    form = PostsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        posts = Posts()
        posts.title = form.title.data
        posts.content = form.content.data
        posts.is_private = form.is_private.data
        current_user.posts.append(posts)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/guestbook')
    return render_template('post.html', title="Создание записи",
                           form=form)


@app.route('/posts/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_posts(id):
    form = PostsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        posts = db_sess.query(Posts).filter(Posts.id == id,
                                            Posts.user == current_user
                                            ).first()
        if posts:
            form.title.data = posts.title
            form.content.data = posts.content
            form.is_private.data = posts.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        posts = db_sess.query(Posts).filter(Posts.id == id,
                                            Posts.user == current_user
                                            ).first()
        if posts:
            posts.title = form.title.data
            posts.content = form.content.data
            posts.is_private = form.is_private.data
            db_sess.commit()
            return redirect('/guestbook')
        else:
            abort(404)
    return render_template('post.html',
                           title='Редактирование записи',
                           form=form
                           )


@app.route('/posts_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def posts_delete(id):
    db_sess = db_session.create_session()
    posts = db_sess.query(Posts).filter(Posts.id == id,
                                        Posts.user == current_user
                                        ).first()
    if posts:
        db_sess.delete(posts)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/guestbook')


def main():
    file_path = os.path.abspath(os.getcwd()) + "/db/guestbook.db"
    db_session.global_init(file_path)
    # для списка объектов
    api.add_resource(posts_resources.PostsListResource, '/api/posts')

    # для одного объекта
    api.add_resource(posts_resources.PostsResource, '/api/posts/<int:posts_id>')

    #
    # app.run(host='0.0.0.0', port=port)
    port = int(os.environ.get("PORT", 5000))
    serve(app, host='0.0.0.0', port=port)

if __name__ == "__main__":
    main()

