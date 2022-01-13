"""Реализация простого Rest API """
from io import BytesIO
from datetime import timedelta
from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, \
    get_jwt_identity
from config import Config

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.from_object(Config)

db = SQLAlchemy(app)
jwt = JWTManager(app)


class Users(db.Model):
    """Создание таблицы Users базы данных"""
    username = db.Column(db.String(30), primary_key=True)
    password = db.Column(db.String(50), nullable=False)


class Todolist(db.Model):
    """Создание таблицы Todolist базы данных"""
    id = db.Column(db.Integer, primary_key=True)
    doings = db.Column(db.Text, nullable=False)
    username = db.Column(db.String(30), db.ForeignKey('users.username'))


class Files(db.Model):
    """Создание таблицы Files базы данных"""
    id = db.Column(db.Integer, primary_key=True)
    filenames = db.Column(db.String(300))
    filesize = db.Column(db.String(30))
    data = db.Column(db.LargeBinary)
    username = db.Column(db.String(30), db.ForeignKey('users.username'))


def get_token(username, expire_time=24):
    """Метод создания и получения токена доступа"""
    token = create_access_token(identity=username,
                                expires_delta=timedelta(expire_time))
    return token


def auth(username, password):
    """Метод для аутентификации пользователя"""
    client = Users.query.filter(Users.username == username).one()
    if not password == client.password:
        raise Exception("error")
    return client


@app.route('/')
def index():
    """Метод показа главной страницы"""
    return {'TODO': 'list'}


@app.route('/user', methods=['POST', 'GET'])
def user():
    """Метод регистрации пользователя"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = Users(username=username, password=password)
        db.session.add(users)
        db.session.commit()
        token = get_token(users.username)
        return {'token': token}
    if request.method == 'GET':
        return {'Sign': 'Up'}
    return {'Error': 'Check request method'}


@app.route('/authentication', methods=['POST', 'GET'])
def authentication():
    """Метод аутентификации пользователя"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = auth(username, password)
        token = get_token(users.username)
        return {'token': token}
    if request.method == 'GET':
        return {'Sign': 'In'}
    return {'Error': 'Check request method'}


@app.route('/todo', methods=['POST', 'GET'])
@jwt_required()
def todo():
    """Метод добавления и просмотра задач"""
    username = get_jwt_identity()
    if request.method == 'POST':
        text = request.form['doings']
        todolist = Todolist(doings=text, username=username)
        db.session.add(todolist)
        db.session.commit()
        return {'status': 'success'}
    if request.method == 'GET':
        items = Todolist.query.filter(Todolist.username == username)
        serialised = []
        for item in items:
            serialised.append({
                'id': item.id,
                'doings': item.doings,
                'username': item.username
            })
        return jsonify(serialised)
    return {'Error': 'Check request method'}


@app.route('/todo/<int:id_user>', methods=['PUT', 'DELETE'])
@jwt_required()
def todo_update(id_user):
    """Метод обновления и удаления задач"""
    username = get_jwt_identity()
    if request.method == 'PUT':
        item = Todolist.query.filter(Todolist.id == id_user,
                                     Todolist.username == username).first()
        text = request.form['doings']
        if not item:
            resp = jsonify({'message': 'No item with this id'})
            resp.status_code = 400
            return resp
        item.doings = text
        db.session.commit()
        return {'status': 'success'}
    if request.method == 'DELETE':
        item = Todolist.query.filter(Todolist.id == id_user,
                                     Todolist.username == username).first()
        if not item:
            resp = jsonify({'message': 'No item with this id'})
            resp.status_code = 400
            return resp
        db.session.delete(item)
        db.session.commit()
        return {'status': 'success'}
    return {'Error': 'Check request method'}


@app.route('/files', methods=['POST', 'GET'])
@jwt_required()
def files():
    """Метод загрузки и просмотра файлов"""
    username = get_jwt_identity()
    if request.method == 'POST':
        file = request.files['file']
        data = file.read()
        size = str(len(data)) + ' byte'
        new_file = Files(filenames=file.filename, filesize=size,
                         data=data, username=username)
        db.session.add(new_file)
        db.session.commit()
        return {'status': 'success'}
    if request.method == 'GET':
        user_files = Files.query.filter(Files.username == username)
        serialised = []
        for file in user_files:
            serialised.append({
                'id': file.id,
                'filename': file.filenames,
                'size': file.filesize
            })
        return jsonify(serialised)
    return {'Error': 'Check request method'}


@app.route('/files/<string:name>', methods=['GET', 'DELETE'])
@jwt_required()
def file_operation(name):
    """Метод скачивания и удаления файлов"""
    username = get_jwt_identity()
    if request.method == 'GET':
        file_data = Files.query.filter(Files.filenames == name,
                                       Files.username == username).first()
        if not file_data:
            return {'message': 'No file with this name'}
        return send_file(BytesIO(file_data.data),
                         attachment_filename=f"{name}", as_attachment=True)
    if request.method == 'DELETE':
        file_data = Files.query.filter(Files.filenames == name,
                                       Files.username == username).first()
        if not file_data:
            return {'message': 'No file with this name'}
        db.session.delete(file_data)
        db.session.commit()
        return {'status': 'success'}
    return {'Error': 'Check request method'}


if __name__ == '__main__':
    app.run(debug=True)
