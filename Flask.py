from flask import Flask, render_template, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
import pyrebase
import BancoDeDados as bd

app = Flask(__name__, template_folder='templates')
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'thisisasecretkey'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

config = {
    'apiKey': "AIzaSyBWC2Qxi4yl3dSh4bnLQGJuSwrRP3i4ML0",
    'authDomain': "user-database-c21a3.firebaseapp.com",
    'projectId': "user-database-c21a3",
    'storageBucket': "user-database-c21a3.appspot.com",
    'messagingSenderId': "543642433638",
    'appId': "1:543642433638:web:da1527f8c5faa9a32ad5a7",
    'databaseURL': ''
}

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()

@login_manager.user_loader
def load_user(user_id):
    return User(user_id, None)


class User(UserMixin):
    def __init__(self, uid, email):
        self.id = uid
        self.email = email

class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(
        min=4, max=40)], render_kw={"placeholder": "Email"})
    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Senha"})
    submit = SubmitField("Registrar")

    def validate_username(self, field):
        try:
            user_info = auth.get_account_info(self.username.data + "@domain.com")
            if user_info:
                raise ValidationError("Email já está em uso")
        except Exception as e:
            pass  # No user found, which is good

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(
        min=4, max=40)], render_kw={"placeholder": "Email"})
    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Senha"})
    submit = SubmitField("Entrar")


@app.route('/')
@login_required
def home():
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = auth.sign_in_with_email_and_password(form.username.data, form.password.data)
            user_id = user['localId']
            user_info = auth.get_account_info(user['idToken'])
            email = user_info['users'][0]['email']
            
            user = User(user_id, email)
            login_user(user)
            return redirect(url_for('home'))
        except Exception as e:
            print(e)  # Handle authentication errors
    return render_template('login.html', form=form)


@app.route('/transporte')
@login_required
def transporte():
    return render_template('transporte.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/mapa')
@login_required
def mapa():
    return render_template('mapa.html')


@app.route('/rotas')
@login_required
def rotas():
    banco = bd.BancoDeDados()
    banco.criar_tabelas()

    # Busca os dados da tabela "PosicoesUsuarios"
    banco.cursor.execute("SELECT * FROM PosicoesUsuarios")
    posicoes = banco.cursor.fetchall()

    # Busca os dados da tabela "Rotas"
    rota1 = banco.get_parada('Rota da manhã')
    print(rota1)

    # Função para determinar o turno com base no horário
    def posicao_turno(horario):
        if horario is not None:
            if horario.split()[1] < '12:00:00':
                return 'manha'
            elif horario.split()[1] < '18:00:00':
                return 'tarde'
            else:
                return 'noite'
        return None

    # Coloque aqui a variável que armazena o turno selecionado (manha, tarde, noite)
    # Por exemplo, você pode mudar para 'tarde' ou 'noite' conforme a seleção do usuário
    selected_content = 'manha'

    banco.__del__()
    return render_template('rotas.html', posicoes=posicoes, rota1=rota1, posicao_turno=posicao_turno, selected_content=selected_content)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        try:
            auth.create_user_with_email_and_password(form.username.data, form.password.data)
            return redirect(url_for('login'))
        except Exception as e:
            print(e)  # Handle registration errors
            
    return render_template('register.html', form=form)


if __name__ == '__main__':
    app.run(debug=True)
    banco = bd.BancoDeDados()
    banco.criar_tabelas()
