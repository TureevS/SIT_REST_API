from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
from config import Config

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.from_object(Config)

db = SQLAlchemy(app)
jwt = JWTManager(app)


class Users(db.Model):
    username = db.Column(db.String(30), primary_key=True)
    password = db.Column(db.String(50), nullable=False)

    def get_token(self, expire_time=24):
        token = create_access_token(identity=self.username, expires_delta=timedelta(expire_time))
        return token

    @classmethod
    def authentication(cls, username, password):
        client = cls.query.filter(cls.username == username).one()
        if not (password == client.password):
            raise Exception("error")
        return client


class Todolist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doings = db.Column(db.Text, nullable=False)
    username = db.Column(db.String(30), db.ForeignKey('users.username'))


@app.route('/')
def index():
    return {'TODO': 'list'}


@app.route('/user', methods=['POST', 'GET'])
def user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = Users(username=username, password=password)

        db.session.add(users)
        db.session.commit()
        token = users.get_token()
        return {'token': token}
    else:
        return {'Sign': 'Up'}


@app.route('/authentication', methods=['POST', 'GET'])
def authentication():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = Users.authentication(username, password)
        token = users.get_token()
        return {'token': token}
    else:
        return {'Sign': 'In'}


@app.route('/todo', methods=['POST', 'GET'])
@jwt_required()
def todo():
    username = get_jwt_identity()
    if request.method == 'POST':
        text = request.form['doings']
        todolist = Todolist(doings=text, username=username)
        db.session.add(todolist)
        db.session.commit()
        return {'status': 'success'}
    elif request.method == 'GET':
        doings = Todolist.query.filter(Todolist.username == username)
        serialised = []
        for do in doings:
            serialised.append({
                'id': do.id,
                'doings': do.doings,
                'username': do.username
            })
        return jsonify(serialised)


@app.route('/todo/<int:id>', methods=['PUT', 'DELETE'])
@jwt_required()
def todo_update(id):
    username = get_jwt_identity()
    if request.method == 'PUT':
        item = Todolist.query.filter(Todolist.id == id, Todolist.username == username).first()
        text = request.form['doings']
        if not item:
            return {'message': 'No item with this id'}, 400
        item.doings = text
        db.session.commit()
        return {'status': 'success'}
    elif request.method == 'DELETE':
        item = Todolist.query.filter(Todolist.id == id, Todolist.username == username).first()
        if not item:
            return {'message': 'No item with this id'}, 400
        db.session.delete(item)
        db.session.commit()
        return {'status': 'success'}


if __name__ == '__main__':
    app.run(debug=True)
