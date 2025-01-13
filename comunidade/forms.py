from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, FileField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from comunidade.models import Usuario
from flask_login import current_user

class FormCriarConta(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    senha = PasswordField('Senha', validators=[DataRequired(), Length(6, 20)])
    confirmacao_senha = PasswordField('Confirmação da Senha', validators=[DataRequired(), EqualTo('senha')])
    botao_submit_criar_conta = SubmitField('Criar Conta')

    # criação de função de validação, devido a importação da biblioteca wtforms.validators a função é chamada
    # mas SEMPRE DEVE SER INICIADA POR validate_ , OBRIGATORIAMENTE

    def validate_email(self, email):
        email_existente = Usuario.query.filter_by(email=email.data).first()
        if email_existente:
            raise ValidationError("E-mail já cadastrado")
    
    # Validação do username
    def validate_username(self, username):
        username_existente = Usuario.query.filter_by(username=username.data).first()
        if username_existente:
            raise ValidationError("Nome de usuário já cadastrado. Por favor, escolha outro.")

class FormLogin(FlaskForm):
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    senha = PasswordField('Senha', validators=[DataRequired(), Length(6, 20)])
    lembrar_dados = BooleanField('Lembrar Dados de Acesso')
    botao_submit_login = SubmitField('Fazer Login')

class FormEditarPerfil(FlaskForm):
    username = StringField('Nome do Usuário', validators=[DataRequired(), Length(3, 50)])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    foto_perfil = FileField('Atualizar Foto de Perfil')
    #####
    curso_excel = BooleanField("Excel Impressionador")
    curso_python = BooleanField("Python Impressionador")
    curso_SQL = BooleanField("SQL Impressionador")
    #####
    submit = SubmitField('Salvar Alterações')

    # Validação para evitar e-mail duplicado
    def validate_email(self, email):
        if email.data != current_user.email:  # Verifica se o e-mail é diferente do atual
            email_existente = Usuario.query.filter_by(email=email.data).first()
            if email_existente:
                raise ValidationError("Este e-mail já está em uso por outro usuário. Por favor, escolha outro.")

    # Validação para evitar nome de usuário duplicado
    def validate_username(self, username):
        if username.data != current_user.username:  # Verifica se o nome é diferente do atual
            username_existente = Usuario.query.filter_by(username=username.data).first()
            if username_existente:
                raise ValidationError("Nome de usuário existente, tente novamente")


class PostForm(FlaskForm):
    titulo = StringField('Título', validators=[DataRequired(), Length(5, 50)])
    corpo = TextAreaField('Assunto', validators=[DataRequired(), Length(2, 10000)])
    submit = SubmitField('Criar Post')
