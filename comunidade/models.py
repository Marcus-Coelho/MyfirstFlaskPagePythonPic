from comunidade import database, login_manager
from datetime import datetime
from flask_login import UserMixin

@login_manager.user_loader # aceno ao login_manager que a função abaixo é a que carrega o usuário
def load_user(user_id):
    return Usuario.query.get(int(user_id))


class Usuario(database.Model, UserMixin): # UserMixin serve para poder reutilizar
    #  uma classe, no caso a classe Usuario, linkando o login_manager
    id = database.Column(database.Integer, primary_key=True)
    username = database.Column(database.String, nullable=False, unique=True)
    email = database.Column(database.String, nullable=False, unique=True)
    senha = database.Column(database.String, nullable=False)
    foto_perfil = database.Column(database.String, default='default.jpg')
    posts = database.relationship('Post', backref='autor', lazy=True)
    cursos = database.Column(database.String, nullable=False, default='Não informado')


class Post(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    titulo = database.Column(database.String, nullable=False)
    corpo = database.Column(database.Text, nullable=False)
    data_criacao = database.Column(database.DateTime, nullable=False, default=datetime.now())
    id_usuario = database.Column(database.Integer, database.ForeignKey('usuario.id'), nullable=False)