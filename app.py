from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask import flash, get_flashed_messages
from datetime import datetime, date
from calendar import monthrange
import json

app = Flask(__name__)
app.secret_key = 'admin123'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///academia.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_admin'

HOLIDAYS_PATH = 'config/holidays.json'

def load_holidays():
    try:
        with open(HOLIDAYS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return set(str(x) for x in data)
    except Exception:
        return set()

def is_holiday(d: date) -> bool:
    return d.isoformat() in load_holidays()

CUTOFF_HOUR = 14

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<Usuario {self.nome}>'

class Aluno(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero_matricula = db.Column(db.String(10), unique=True, nullable=False)
    numero_aluno = db.Column(db.String(10), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    idade = db.Column(db.Integer, nullable=False)
    endereco = db.Column(db.String(150), nullable=False)
    bairro = db.Column(db.String(100), nullable=False)
    cidade = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(2), nullable=False)
    cep = db.Column(db.String(10), nullable=False)
    nacionalidade = db.Column(db.String(50), nullable=False)
    data_nascimento = db.Column(db.String(10), nullable=False)
    cpf = db.Column(db.String(14), nullable=False)
    rg = db.Column(db.String(20), nullable=False)
    estado_civil = db.Column(db.String(20), nullable=False)
    nome_conjuge = db.Column(db.String(100), nullable=True)
    sexo = db.Column(db.String(1), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    nome_pai = db.Column(db.String(100), nullable=False)
    nome_mae = db.Column(db.String(100), nullable=False)
    faixa = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f'<Aluno {self.nome}>'

class Admin(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    senha_hash = db.Column(db.String(128), nullable=False)

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

class Horario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dia_semana = db.Column(db.String(20), nullable=False)
    hora = db.Column(db.String(5), nullable=False)
    faixa = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f"<Horario {self.dia_semana} {self.hora} - {self.faixa}>"

class Agendamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    aluno_id = db.Column(db.Integer, db.ForeignKey('aluno.id'), nullable=False)
    horario_id = db.Column(db.Integer, db.ForeignKey('horario.id'), nullable=False)

    aluno = db.relationship('Aluno', backref='agendamentos')
    horario = db.relationship('Horario', backref='agendamentos')


@login_manager.user_loader
def load_user(admin_id):
    return Admin.query.get(int(admin_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/acessar_aluno', methods=['GET', 'POST'])
def acessar_aluno():
    aluno = None
    if request.method == 'POST':
        matricula = request.form['matricula']
        senha = request.form['senha']

        aluno = Aluno.query.filter_by(numero_matricula=matricula).first()
        if aluno and aluno.cpf.replace('.', '').replace('-', '')[:4] == senha:
            return render_template('acessar_aluno.html',
                                   aluno=aluno,
                                   CUTOFF_HOUR=CUTOFF_HOUR,
                                   NOW_HOUR=datetime.now().hour)

        flash('Matrícula ou senha inválidos!', 'danger')
    return render_template('acessar_aluno.html',
                           aluno=aluno,
                           CUTOFF_HOUR=CUTOFF_HOUR,
                           NOW_HOUR=datetime.now().hour)

@app.route('/login_admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        admin = Admin.query.filter_by(email=email).first()
        if admin and admin.verificar_senha(senha):
            login_user(admin)
            return redirect(url_for('admin_painel'))
        else:
            flash('Email ou senha incorretos!', 'danger')

    return render_template('login_admin.html')

@app.route('/login_aluno', methods=['GET', 'POST'])
def login_aluno():
    if request.method == 'POST':
        matricula = request.form['matricula']
        senha = request.form['senha']

        aluno = Aluno.query.filter_by(numero_matricula=matricula).first()
        if aluno and aluno.cpf.replace('.', '').replace('-', '')[:4] == senha:
            faixa = aluno.faixa
            horarios = Horario.query.filter_by(faixa=faixa).all()
            return render_template('horarios_aluno.html',
                                   aluno=aluno,
                                   horarios=horarios,
                                   CUTOFF_HOUR=CUTOFF_HOUR)
        else:
            flash('Matrícula ou senha inválidos!', 'danger')

    return render_template('login_aluno.html')

@app.route('/cadastro_admin', methods=['GET', 'POST'])
def cadastro_admin():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        novo_admin = Admin(email=email)
        novo_admin.set_senha(senha)

        db.session.add(novo_admin)
        db.session.commit()

        flash('Administrador cadastrado com sucesso!', 'success')
        return redirect(url_for('login_admin'))

    return render_template('cadastro_admin.html')

horarios_validos = {
    'Segunda':   ['08:30', '09:30', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00'],
    'Terça':     ['09:30', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00'],
    'Quarta':    ['09:30', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00'],
    'Quinta':    ['08:30', '09:30', '16:00', '17:00', '18:00', '19:00', '20:00'],
    'Sexta':     ['09:30', '17:00', '18:00', '19:00'],
    'Sábado':    ['09:00', '10:00', '11:00', '12:00']
}

@app.route('/cadastrar_horario', methods=['GET', 'POST'])
def cadastrar_horario():
    if request.method == 'GET':
        aluno_id = request.args.get('aluno_id', type=int)
        if not aluno_id:
            flash('Aluno não identificado.', 'warning')
            return redirect(url_for('acessar_aluno'))

        aluno = Aluno.query.get_or_404(aluno_id)
        return render_template('cadastrar_horario.html', aluno=aluno)

    elif request.method == 'POST':
        aluno_id = request.form.get('aluno_id')
        dia_semana = request.form.get('dia_semana')
        hora = request.form.get('hora')
        faixa = request.form.get('faixa')

        if not aluno_id:
            flash('Aluno não identificado!', 'danger')
            return redirect(url_for('acessar_aluno'))

        if not dia_semana or not hora or not faixa:
            flash('Preencha todos os campos para continuar o agendamento.', 'warning')
            return redirect(url_for('cadastrar_horario', aluno_id=aluno_id))

        hoje = datetime.now()
        dia_semana_atual = hoje.strftime('%A')
        mapa_dias = {
            'Monday': 'Segunda',
            'Tuesday': 'Terça',
            'Wednesday': 'Quarta',
            'Thursday': 'Quinta',
            'Friday': 'Sexta',
            'Saturday': 'Sábado',
            'Sunday': 'Domingo'
        }
        dia_atual_portugues = mapa_dias[dia_semana_atual]

        if dia_semana == dia_atual_portugues and dia_semana != 'Sábado':
            if hoje.hour >= 14:
                flash('Regra de agendamento: para aulas no mesmo dia (segunda a sexta), o agendamento deve ser feito até as 14h.', 'danger')
                return redirect(url_for('meus_agendamentos', aluno_id=aluno_id))

        if dia_semana == 'Sábado':
            if not (dia_atual_portugues == 'Sexta' and 16 <= hoje.hour < 20):
                flash('Regra de agendamento: aulas de sábado só podem ser agendadas na sexta-feira, entre 16h e 20h.', 'danger')
                return redirect(url_for('meus_agendamentos', aluno_id=aluno_id))

        horario = Horario.query.filter_by(dia_semana=dia_semana, hora=hora, faixa=faixa).first()
        if not horario:
            horario = Horario(dia_semana=dia_semana, hora=hora, faixa=faixa)
            db.session.add(horario)
            db.session.commit()

        ja_existe = Agendamento.query.filter_by(aluno_id=aluno_id, horario_id=horario.id).first()
        if ja_existe:
            flash('Você já possui um agendamento nesse horário!', 'warning')
            return redirect(url_for('meus_agendamentos', aluno_id=aluno_id))

        agendamento = Agendamento(aluno_id=aluno_id, horario_id=horario.id)
        db.session.add(agendamento)
        db.session.commit()

        flash('Horário cadastrado com sucesso!', 'success')
        return redirect(url_for('meus_agendamentos', aluno_id=aluno_id))

@app.route('/meus_agendamentos/<int:aluno_id>')
def meus_agendamentos(aluno_id):
    aluno = Aluno.query.get_or_404(aluno_id)
    agendamentos = Agendamento.query.filter_by(aluno_id=aluno.id).all()
    return render_template('meus_agendamentos.html', aluno=aluno, agendamentos=agendamentos)

@app.route('/admin_painel')
@login_required
def admin_painel():
    return render_template('admin_painel.html')

@app.route('/novo_aluno', methods=['GET', 'POST'])
@login_required
def novo_aluno():
    if request.method == 'POST':
        numero_aluno = request.form['numero_aluno']

        aluno_existente = Aluno.query.filter_by(numero_aluno=numero_aluno).first()
        if aluno_existente:
            flash(f'Número do aluno "{numero_aluno}" já está cadastrado!', 'danger')
            return render_template('novo_aluno.html')

        ultimo_aluno = Aluno.query.order_by(Aluno.id.desc()).first()
        if ultimo_aluno and ultimo_aluno.numero_matricula.isdigit():
            nova_matricula = str(int(ultimo_aluno.numero_matricula) + 1).zfill(3)
        else:
            nova_matricula = "001"

        aluno = Aluno(
            numero_matricula=nova_matricula,
            numero_aluno=numero_aluno,
            nome=request.form['nome'],
            idade=request.form['idade'],
            endereco=request.form['endereco'],
            bairro=request.form['bairro'],
            cidade=request.form['cidade'],
            estado=request.form['estado'],
            cep=request.form['cep'],
            nacionalidade=request.form['nacionalidade'],
            data_nascimento=request.form['data_nascimento'],
            cpf=request.form['cpf'],
            rg=request.form['rg'],
            estado_civil=request.form['estado_civil'],
            nome_conjuge=request.form.get('nome_conjuge', ''),
            sexo=request.form['sexo'],
            telefone=request.form['telefone'],
            email=request.form['email'],
            nome_pai=request.form['nome_pai'],
            nome_mae=request.form['nome_mae'],
            faixa=request.form['faixa']
        )

        db.session.add(aluno)
        db.session.commit()

        flash(f'Aluno cadastrado com matrícula {nova_matricula}!', 'success')
        return redirect(url_for('listar_alunos'))

    return render_template('novo_aluno.html')

@app.route('/listar_alunos')
@login_required
def listar_alunos():
    alunos = Aluno.query.all()
    return render_template('listar_alunos.html', alunos=alunos)

@app.route('/listar_horarios')
@login_required
def listar_horarios():
    horarios = Horario.query.all()
    return render_template('listar_horarios.html', horarios=horarios)

@app.route('/excluir_horario/<int:horario_id>')
@login_required
def excluir_horario(horario_id):
    horario = Horario.query.get_or_404(horario_id)
    db.session.delete(horario)
    db.session.commit()
    flash('Horário excluído com sucesso!', 'success')
    return redirect(url_for('listar_horarios'))

@app.route('/agendar_aula/<int:aluno_id>', methods=['POST'])
def agendar_aula(aluno_id):
    horario_id = request.form['horario_id']
    aluno = Aluno.query.get_or_404(aluno_id)

    agendamento_existente = Agendamento.query.filter_by(aluno_id=aluno_id, horario_id=horario_id).first()
    if agendamento_existente:
        faixa = aluno.faixa
        horarios = Horario.query.filter_by(faixa=faixa).all()
        flash('Você já agendou esse horário!', 'danger')
        return render_template('horarios_aluno.html',
                               aluno=aluno,
                               horarios=horarios,
                               CUTOFF_HOUR=CUTOFF_HOUR)

    horario_escolhido = Horario.query.get_or_404(horario_id)
    hoje = datetime.now()
    weekday_map = {0: 'Segunda', 1: 'Terça', 2: 'Quarta', 3: 'Quinta', 4: 'Sexta', 5: 'Sábado', 6: 'Domingo'}
    hoje_nome = weekday_map[hoje.weekday()]
    if hoje_nome == horario_escolhido.dia_semana and hoje.hour >= CUTOFF_HOUR:
        faixa = aluno.faixa
        horarios = Horario.query.filter_by(faixa=faixa).all()
        flash(f'Agendamento para hoje só permitido até as {CUTOFF_HOUR}:00.', 'danger')
        return render_template('horarios_aluno.html',
                               aluno=aluno,
                               horarios=horarios,
                               CUTOFF_HOUR=CUTOFF_HOUR)

    novo_agendamento = Agendamento(aluno_id=aluno_id, horario_id=horario_id)
    db.session.add(novo_agendamento)
    db.session.commit()

    flash('Aula agendada com sucesso!', 'success')
    return redirect(url_for('index'))

@app.route('/editar_horario/<int:horario_id>', methods=['GET', 'POST'])
@login_required
def editar_horario(horario_id):
    horario = Horario.query.get_or_404(horario_id)

    if request.method == 'POST':
        horario.dia_semana = request.form['dia_semana']
        horario.hora = request.form['hora']
        horario.faixa = request.form['faixa']

        db.session.commit()
        flash('Horário atualizado com sucesso!', 'success')
        return redirect(url_for('listar_horarios'))

    return render_template('editar_horario.html', horario=horario)

@app.route('/listar_agendamentos')
@login_required
def listar_agendamentos():
    agendamentos = Agendamento.query.all()
    return render_template('listar_agendamentos.html', agendamentos=agendamentos)

@app.route('/excluir_aluno/<int:aluno_id>')
@login_required
def excluir_aluno(aluno_id):
    aluno = Aluno.query.get_or_404(aluno_id)
    db.session.delete(aluno)
    db.session.commit()
    return redirect(url_for('listar_alunos'))

@app.route('/editar_aluno/<int:aluno_id>', methods=['GET', 'POST'])
@login_required
def editar_aluno(aluno_id):
    aluno = Aluno.query.get_or_404(aluno_id)

    if request.method == 'POST':
        aluno.nome = request.form['nome']
        aluno.idade = request.form['idade']
        aluno.email = request.form['email']
        senha = request.form['senha']

        if senha:
            aluno.set_senha(senha)

        db.session.commit()
        return redirect(url_for('listar_alunos'))

    return render_template('editar_aluno.html', aluno=aluno)

@app.route('/relatorio_agendamentos', methods=['GET', 'POST'])
@login_required
def relatorio_agendamentos():
    filtro_dia = request.args.get('dia_semana')
    filtro_hora = request.args.get('hora')
    filtro_faixa = request.args.get('faixa')

    query = Agendamento.query.join(Aluno).join(Horario)

    if filtro_dia:
        query = query.filter(Horario.dia_semana == filtro_dia)
    if filtro_hora:
        query = query.filter(Horario.hora == filtro_hora)
    if filtro_faixa:
        query = query.filter(Horario.faixa == filtro_faixa)

    agendamentos = query.all()

    return render_template(
        'relatorio_agendamentos.html',
        agendamentos=agendamentos,
        filtro_dia=filtro_dia,
        filtro_hora=filtro_hora,
        filtro_faixa=filtro_faixa
    )

@app.route('/calendar')
def calendar_view():
    today = datetime.now().date()
    holidays_list = sorted(load_holidays())
    return render_template('calendar.html', year=today.year, month=today.month, holidays=holidays_list)

@app.route('/api/available-days')
def api_available_days():
    try:
        year = int(request.args.get('year'))
        month = int(request.args.get('month'))
    except (TypeError, ValueError):
        today = datetime.now().date()
        year, month = today.year, today.month

    _, last_day = monthrange(year, month)
    available = []
    for day in range(1, last_day + 1):
        d = date(year, month, day)
        if d.weekday() == 6:
            continue
        if is_holiday(d):
            continue
        available.append(d.isoformat())

    return {'year': year, 'month': month, 'available_days': available, 'holidays': sorted(load_holidays())}

@app.route('/editar_calendario', methods=['GET', 'POST'])
@login_required
def editar_calendario():
    if not current_user.is_authenticated:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('index'))

    holidays = sorted(load_holidays())

    if request.method == 'POST':
        nova_data = request.form.get('data')
        if nova_data:
            hs = load_holidays()
            hs.add(nova_data)
            with open(HOLIDAYS_PATH, 'w', encoding='utf-8') as f:
                json.dump(sorted(hs), f, indent=2, ensure_ascii=False)
            flash(f'Feriado {nova_data} adicionado com sucesso!', 'success')
        return redirect(url_for('editar_calendario'))

    return render_template('editar_calendario.html', holidays=holidays)

@app.route('/remover_feriado/<data>')
@login_required
def remover_feriado(data):
    hs = load_holidays()
    if data in hs:
        hs.remove(data)
        with open(HOLIDAYS_PATH, 'w', encoding='utf-8') as f:
            json.dump(sorted(hs), f, indent=2, ensure_ascii=False)
        flash(f'Feriado {data} removido com sucesso!', 'success')
    else:
        flash('Data não encontrada.', 'warning')
    return redirect(url_for('editar_calendario'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
