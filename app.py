# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from sqlalchemy import func, or_, and_
from functools import wraps
import os
import uuid
from flask_migrate import Migrate
import time
import stripe
from flask_mail import Mail, Message
from config import Config
from sqlalchemy import text

# Configuração do Stripe
stripe.api_key = 'sk_test_51QbVcLKxtlwVKoGi0AuzhFm6FmgCDnwZPmMZMCKYuBmex3wb4N9yIcOTubCJb9GGpF37zBnX1YZqeo7fd68GGyHX00j2yH2KeX'
STRIPE_PUBLIC_KEY = 'pk_test_51QbVcLKxtlwVKoGi1mssIKeOby7ZtYayRV9ZdE9aXJkbeK00RKHbExzi8lvcnuomDOhdNoJFoh5lCmV3MwTKBLWV00KRz3Fpue'

app = Flask(__name__)
app.config.from_object(Config)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///donate.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# Cria a pasta de uploads se não existir
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Configuração do banco de dados
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Configuração do login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Configuração do email
mail = Mail(app)

# Modelos
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False)
    is_blocked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    profile_image = db.Column(db.String(100))
    pix_key = db.Column(db.String(100), nullable=True)
    campaigns = db.relationship('Campaign', backref='user', lazy=True)
    donations = db.relationship('Donation', backref='donor', lazy=True)
    likes = db.relationship('Like', backref='user', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)
    campaign_views = db.relationship('CampaignView', backref='user', lazy=True)
    # Relações para WithdrawalRequest
    requested_withdrawals = db.relationship('WithdrawalRequest',
                                          foreign_keys='WithdrawalRequest.user_id',
                                          backref='requester',
                                          lazy=True)
    processed_withdrawals = db.relationship('WithdrawalRequest',
                                          foreign_keys='WithdrawalRequest.processed_by_id',
                                          backref='processor',
                                          lazy=True)

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    goal = db.Column(db.Float)
    image = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    allow_comments = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)  # Nova coluna
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    donations = db.relationship('Donation', backref='campaign', lazy=True)
    withdrawal_requests = db.relationship('WithdrawalRequest', backref='campaign', lazy=True)
    comments = db.relationship('Comment', backref='campaign', lazy=True, cascade='all, delete-orphan')
    campaign_views = db.relationship('CampaignView', backref='campaign', lazy=True)
    likes = db.relationship('Like', backref='campaign', lazy=True)
    
    @property
    def total_donated(self):
        return sum(d.amount for d in self.donations)
    
    @property
    def total_net(self):
        return sum(d.net_amount for d in self.donations)
    
    @property
    def total_withdrawn(self):
        return sum(w.amount for w in self.withdrawal_requests if w.status == 'approved') or 0
    
    @property
    def available_for_withdrawal(self):
        return self.total_net - self.total_withdrawn
    
    @property
    def image_url(self):
        return self.image
    
    @property
    def current_amount(self):
        """Compatibilidade com o template antigo"""
        return self.total_donated
    
    @property
    def progress_percentage(self):
        """Calcula a porcentagem de progresso da meta"""
        if not self.goal or self.goal <= 0:
            return 0
        return min(100, (self.total_donated / self.goal) * 100)
    
    @property
    def views(self):
        """Retorna o número total de visualizações da campanha"""
        return len(self.campaign_views)

class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    net_amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    # Garante que cada usuário só pode curtir uma vez
    __table_args__ = (
        db.UniqueConstraint('user_id', 'campaign_id', name='unique_user_like'),
    )

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)

class CampaignView(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)  # Permitir NULL para o IP
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)

class WithdrawalRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    fee_percentage = db.Column(db.Float, nullable=False)
    net_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    processed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    notes = db.Column(db.Text)
    next_attempt_allowed_at = db.Column(db.DateTime, nullable=True)
    pix_key = db.Column(db.String(100), nullable=True)  # Nova coluna

class SystemConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    withdrawal_fee = db.Column(db.Float, default=5.0)
    min_withdrawal_percentage = db.Column(db.Float, default=10.0)
    next_withdrawal_minutes = db.Column(db.Integer, default=1440)  # 24 horas em minutos
    gateway_fee_percentage = db.Column(db.Float, default=3.99)  # Taxa percentual do gateway (%)
    gateway_fee_fixed = db.Column(db.Float, default=0.39)  # Taxa fixa do gateway (R$)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    updated_by = db.relationship('User')

# Funções auxiliares
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def format_datetime(value):
    if value is None:
        return ""
    return value.strftime("%d/%m/%Y %H:%M")

@app.template_filter('format_datetime')
def format_datetime(value):
    if value is None:
        return ""
    return value.strftime("%d/%m/%Y %H:%M")

@app.template_filter('format_currency_br')
def format_currency_br(value):
    if value is None:
        return "R$ 0,00"
    try:
        value = float(value)
        int_part = int(value)
        decimal_part = int((value - int_part) * 100)
        str_int = str(int_part)
        groups = []
        while str_int:
            groups.insert(0, str_int[-3:])
            str_int = str_int[:-3]
        formatted_int = '.'.join(groups)
        return f"R$ {formatted_int},{decimal_part:02d}"
    except:
        return "R$ 0,00"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def get_waiting_time_for_withdrawal(campaign):
    """Calcula o tempo de espera restante para próxima retirada"""
    last_rejected = WithdrawalRequest.query.filter_by(
        campaign_id=campaign.id,
        status='rejected'
    ).order_by(WithdrawalRequest.created_at.desc()).first()
    
    if last_rejected:
        config = SystemConfig.query.first()
        next_withdrawal_minutes = config.next_withdrawal_minutes if config else 1440
        time_since_reject = datetime.utcnow() - last_rejected.processed_at
        
        if time_since_reject.total_seconds() < (next_withdrawal_minutes * 60):
            return int(next_withdrawal_minutes - (time_since_reject.total_seconds() / 60))
    
    return None

# Rotas
@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 6  # Número de campanhas por página
    search = request.args.get('search', '')
    status = request.args.get('status', 'active')  # Default é mostrar campanhas ativas
    
    # Iniciar a query base
    query = Campaign.query
    
    # Aplicar filtro de busca
    if search:
        query = query.filter(Campaign.title.ilike(f'%{search}%'))
    
    # Aplicar filtro de status
    now = datetime.now()
    if status == 'active':
        query = query.filter(Campaign.is_active == True)
        query = query.filter(or_(Campaign.end_date == None, Campaign.end_date > now))
    elif status == 'inactive':
        query = query.filter(or_(Campaign.is_active == False, 
                               and_(Campaign.end_date != None, Campaign.end_date <= now)))
    
    # Ordenar por data de criação
    query = query.order_by(Campaign.created_at.desc())
    
    # Executar paginação
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    campaigns = pagination.items
    
    # Calcular estatísticas totais
    total_stats = {
        'total_campaigns': Campaign.query.count(),
        'total_donated': db.session.query(func.sum(Donation.amount)).scalar() or 0,
        'total_views': db.session.query(CampaignView).count()
    }
    
    return render_template(
        'index.html',
        campaigns=campaigns,
        pagination=pagination,
        total_stats=total_stats,
        current_year=datetime.now().year,
        now=now
    )

@app.route('/about')
def about():
    return render_template('about.html', current_year=datetime.now().year)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        try:
            msg = Message(
                subject=f'Contato do Site: {subject}',
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=[app.config['CONTACT_EMAIL']],
                reply_to=email,
                body=f'''
Nova mensagem de contato:

Nome: {name}
Email: {email}
Telefone: {phone}
Assunto: {subject}

Mensagem:
{message}
''')
            
            mail.send(msg)
            
            flash('Sua mensagem foi enviada com sucesso! Entraremos em contato em breve.', 'success')
        except Exception as e:
            error_msg = str(e)
            flash(f'Erro ao enviar mensagem: {error_msg}', 'error')
            app.logger.error(f'Erro ao enviar email: {error_msg}')
        
        return redirect(url_for('contact'))
    
    return render_template('contact.html', current_year=datetime.now().year)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        if 'profile_image' in request.files:
            file = request.files['profile_image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                current_user.profile_image = filename
                db.session.commit()
                flash('Foto de perfil atualizada com sucesso!', 'success')
        
        pix_key = request.form.get('pix_key')
        if pix_key is not None:
            current_user.pix_key = pix_key
            db.session.commit()
            flash('Chave PIX atualizada com sucesso!', 'success')
        
        return redirect(url_for('profile'))
    
    total_campaigns = Campaign.query.filter_by(user_id=current_user.id).count()
    total_donations = Donation.query.filter_by(user_id=current_user.id).count()
    total_likes = Like.query.filter_by(user_id=current_user.id).count()
    
    return render_template('profile.html', 
                         total_campaigns=total_campaigns,
                         total_donations=total_donations,
                         total_likes=total_likes,
                         current_year=datetime.now().year)

@app.route('/my_campaigns')
@login_required
def my_campaigns():
    campaigns = Campaign.query.filter_by(user_id=current_user.id).all()
    return render_template('my_campaigns.html', campaigns=campaigns)

@app.route('/my_donations')
@login_required
def my_donations():
    donations = Donation.query.filter_by(user_id=current_user.id).order_by(Donation.created_at.desc()).all()
    total_donated = sum(donation.amount for donation in donations)
    return render_template('my_donations.html', donations=donations, total_donated=total_donated, current_year=datetime.now().year)

@app.route('/new_campaign', methods=['GET', 'POST'])
@login_required
def new_campaign():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        goal = float(request.form.get('goal').replace('R$', '').replace('.', '').replace(',', '.'))
        
        campaign = Campaign(
            title=title,
            description=description,
            goal=goal,
            user_id=current_user.id
        )
        
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = int(time.time())
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                campaign.image = filename
        
        db.session.add(campaign)
        db.session.commit()
        
        flash('Campanha criada com sucesso!', 'success')
        return redirect(url_for('campaign', campaign_id=campaign.id))
    
    return render_template('new_campaign.html', current_year=datetime.now().year)

@app.route('/user_likes')
@login_required
def user_likes():
    liked_campaigns = Campaign.query\
        .join(Like)\
        .filter(Like.user_id == current_user.id)\
        .order_by(Like.created_at.desc())\
        .all()
    
    return render_template('user_likes.html', 
                         campaigns=liked_campaigns, 
                         current_year=datetime.now().year)

@app.route('/admin_dashboard')
@login_required
@admin_required
def admin_dashboard():
    total_users = User.query.count()
    total_campaigns = Campaign.query.count()
    total_donations = Donation.query.count()
    total_amount = db.session.query(db.func.sum(Donation.amount)).scalar() or 0
    
    users = User.query.order_by(User.username).all()
    
    recent_campaigns = Campaign.query.order_by(Campaign.created_at.desc()).limit(10).all()
    
    return render_template('admin_dashboard.html',
                         total_users=total_users,
                         total_campaigns=total_campaigns,
                         total_donations=total_donations,
                         total_amount=total_amount,
                         recent_campaigns=recent_campaigns,
                         users=users,
                         current_year=datetime.now().year)

@app.route('/admin/toggle_admin/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'Você não pode remover seus próprios privilégios de administrador'})
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Status de administrador alterado para {user.username}'
    })

@app.route('/admin/toggle_block/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_block(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.is_admin:
        return jsonify({'success': False, 'message': 'Não é possível bloquear um administrador'})
    
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'Você não pode bloquear a si mesmo'})
    
    user.is_blocked = not user.is_blocked
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Status de bloqueio alterado para {user.username}'
    })

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Nome de usuário já existe', 'error')
            return redirect(url_for('register'))
            
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email já está em uso', 'error')
            return redirect(url_for('register'))
            
        new_user = User(username=username, email=email)
        new_user.password_hash = generate_password_hash(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Cadastro realizado com sucesso!', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            if user.is_blocked:
                flash('Sua conta está bloqueada. Entre em contato com o administrador.', 'error')
                return redirect(url_for('login'))
            
            login_user(user)
            return redirect(url_for('index'))
            
        flash('Usuário ou senha inválidos', 'error')
    
    return render_template('login.html', current_year=datetime.now().year)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/campaign/<int:campaign_id>')
def campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    donations = Donation.query.filter_by(campaign_id=campaign_id).order_by(Donation.created_at.desc()).all()
    comments = Comment.query.filter_by(campaign_id=campaign_id).order_by(Comment.created_at.desc()).all()
    
    # Registra visualização
    if current_user.is_authenticated and current_user.id != campaign.user_id:
        view = CampaignView(
            campaign_id=campaign_id,
            user_id=current_user.id,
            ip_address=request.remote_addr
        )
        db.session.add(view)
        try:
            db.session.commit()
        except:
            db.session.rollback()
    
    # Verifica se o usuário atual já curtiu
    user_liked = False
    if current_user.is_authenticated:
        like = Like.query.filter_by(
            campaign_id=campaign_id,
            user_id=current_user.id
        ).first()
        user_liked = like is not None
    
    # Busca configurações do sistema
    config = SystemConfig.query.first()
    withdrawal_fee = config.withdrawal_fee if config else 5.0
    
    # Calcula valores
    total_donated = campaign.total_donated
    total_net = campaign.total_net
    available_for_withdrawal = campaign.available_for_withdrawal
    
    return render_template('campaign.html',
                         campaign=campaign,
                         donations=donations,
                         comments=comments,
                         user_liked=user_liked,
                         total_donated=total_donated,
                         total_net=total_net,
                         available_for_withdrawal=available_for_withdrawal,
                         withdrawal_fee=withdrawal_fee,
                         now=datetime.utcnow())

@app.route('/campaign/<int:campaign_id>/donate', methods=['POST'])
@login_required
def donate(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    
    # Verifica se a campanha está ativa
    if not campaign.is_active:
        flash('Esta campanha foi encerrada e não está mais aceitando doações.', 'error')
        return redirect(url_for('campaign', campaign_id=campaign_id))
    
    if campaign.end_date:
        flash('Esta campanha foi encerrada e não está mais aceitando doações.', 'error')
        return redirect(url_for('campaign', campaign_id=campaign_id))
    
    try:
        # Trata o valor da doação, removendo R$ e substituindo vírgula por ponto
        amount_str = request.form.get('amount', '0')
        amount_str = amount_str.replace('R$', '').replace('.', '').replace(',', '.')
        amount = float(amount_str)
        
        if amount <= 0:
            flash('O valor da doação deve ser maior que zero.', 'error')
            return redirect(url_for('campaign', campaign_id=campaign_id))
        
        # Calcula as taxas do gateway
        config = SystemConfig.query.first()
        if config:
            gateway_fee = (amount * config.gateway_fee_percentage / 100) + config.gateway_fee_fixed
            net_amount = amount - gateway_fee
        else:
            net_amount = amount
            
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'brl',
                        'unit_amount': int(amount * 100),  # Stripe usa centavos
                        'product_data': {
                            'name': f'Doação para: {campaign.title}',
                            'description': f'Campanha criada por {campaign.user.username}',
                        },
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=url_for('donation_success', campaign_id=campaign_id, amount=amount, net_amount=net_amount, _external=True),
                cancel_url=url_for('donation_cancel', campaign_id=campaign_id, _external=True),
                metadata={
                    'campaign_id': campaign_id,
                    'user_id': current_user.id,
                    'amount': amount,
                    'net_amount': net_amount
                }
            )
            return redirect(checkout_session.url, code=303)
        except Exception as e:
            app.logger.error(f"Erro Stripe: {str(e)}")
            flash('Erro ao processar pagamento. Por favor, tente novamente.', 'error')
            return redirect(url_for('campaign', campaign_id=campaign_id))
            
    except ValueError:
        flash('Por favor, insira um valor válido para a doação.', 'error')
    except Exception as e:
        flash('Erro ao processar doação. Por favor, tente novamente.', 'error')
        app.logger.error(f'Erro ao processar doação: {str(e)}')
    
    return redirect(url_for('campaign', campaign_id=campaign_id))

@app.route('/donation/success/<int:campaign_id>')
@login_required
def donation_success(campaign_id):
    amount = float(request.args.get('amount', 0))
    net_amount = float(request.args.get('net_amount', 0))
    
    donation = Donation(
        campaign_id=campaign_id,
        user_id=current_user.id,
        amount=amount,
        net_amount=net_amount
    )
    
    db.session.add(donation)
    db.session.commit()
    
    flash('Doação realizada com sucesso! Obrigado por ajudar.', 'success')
    return redirect(url_for('campaign', campaign_id=campaign_id))

@app.route('/donation/cancel/<int:campaign_id>')
@login_required
def donation_cancel(campaign_id):
    flash('Doação cancelada.', 'info')
    return redirect(url_for('campaign', campaign_id=campaign_id))

@app.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, 'seu_webhook_secret'
        )
    except ValueError as e:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        return 'Invalid signature', 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        campaign_id = session['metadata']['campaign_id']
        user_id = session['metadata']['user_id']
        amount = float(session['metadata']['amount'])
        
        campaign = Campaign.query.get(campaign_id)
        if campaign:
            donation = Donation(
                amount=amount,
                user_id=user_id,
                campaign_id=campaign_id
            )
            campaign.current_amount += amount
            db.session.add(donation)
            db.session.commit()

    return '', 200

@app.route('/campaign/<int:campaign_id>/like', methods=['POST'])
@login_required
def toggle_like(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    
    like = Like.query.filter_by(
        user_id=current_user.id,
        campaign_id=campaign_id
    ).first()
    
    if like:
        db.session.delete(like)
        liked = False
    else:
        like = Like(user_id=current_user.id, campaign_id=campaign_id)
        db.session.add(like)
        liked = True
    
    db.session.commit()
    
    total_likes = Like.query.filter_by(campaign_id=campaign_id).count()
    
    return jsonify({
        'liked': liked,
        'count': total_likes
    })

@app.route('/campaign/<int:campaign_id>/comment', methods=['POST'])
@login_required
def add_comment(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    
    if not campaign.allow_comments:
        flash('Comentários estão desativados para esta campanha', 'error')
        return redirect(url_for('campaign', campaign_id=campaign_id))
    
    content = request.form.get('content')
    if not content:
        flash('O comentário não pode estar vazio', 'error')
        return redirect(url_for('campaign', campaign_id=campaign_id))
    
    comment = Comment(content=content, author=current_user, campaign=campaign)
    db.session.add(comment)
    db.session.commit()
    
    flash('Comentário adicionado com sucesso!', 'success')
    return redirect(url_for('campaign', campaign_id=campaign_id))

@app.route('/campaign/<int:campaign_id>/image/remove', methods=['POST'])
@login_required
def remove_campaign_image(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    
    if campaign.user_id != current_user.id:
        flash('Você não tem permissão para alterar esta campanha.', 'error')
        return redirect(url_for('campaign', campaign_id=campaign_id))
    
    try:
        # Remove o arquivo antigo se existir
        if campaign.image and campaign.image != 'default_campaign.jpg':
            old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], campaign.image)
            if os.path.exists(old_image_path):
                os.remove(old_image_path)
        
        # Define a imagem padrão
        campaign.image = None
        db.session.commit()
        flash('Imagem removida com sucesso!', 'success')
    except Exception as e:
        app.logger.error(f'Erro ao remover imagem: {str(e)}')
        flash('Erro ao remover imagem. Tente novamente.', 'error')
    
    return redirect(url_for('campaign', campaign_id=campaign_id))

@app.route('/update_profile_photo', methods=['POST'])
@login_required
def update_profile_photo():
    if 'photo' not in request.files:
        flash('Nenhuma foto enviada', 'error')
        return redirect(url_for('profile'))
    
    photo = request.files['photo']
    if photo.filename == '':
        flash('Nenhuma foto selecionada', 'error')
        return redirect(url_for('profile'))
    
    if photo and allowed_file(photo.filename):
        filename = secure_filename(f"{current_user.username}_{int(time.time())}_{photo.filename}")
        profiles_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'profiles')
        if not os.path.exists(profiles_folder):
            os.makedirs(profiles_folder)
        
        photo_path = os.path.join(profiles_folder, filename)
        photo.save(photo_path)
        
        current_user.profile_image = 'profiles/' + filename
        db.session.commit()
        
        flash('Foto de perfil atualizada com sucesso!', 'success')
    else:
        flash('Tipo de arquivo não permitido', 'error')
    
    return redirect(url_for('profile'))

@app.route('/campaign/<int:campaign_id>/donations')
@login_required
def donation_history(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    if current_user.id != campaign.user_id and not current_user.is_admin:
        abort(403)
    
    donations = Donation.query.filter_by(campaign_id=campaign_id)\
        .order_by(Donation.created_at.desc()).all()
    
    total_amount = sum(donation.amount for donation in donations)
    
    return render_template('donation_history.html', 
                         campaign=campaign, 
                         donations=donations,
                         total_amount=total_amount,
                         current_year=datetime.now().year)

# Rotas de Retirada
@app.route('/request_withdrawal/<int:campaign_id>', methods=['POST'])
@login_required
def request_withdrawal(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    
    # Verificar se o usuário é o dono da campanha
    if campaign.user_id != current_user.id:
        flash('Você não tem permissão para solicitar retirada desta campanha.', 'error')
        return redirect(url_for('campaign', campaign_id=campaign_id))
    
    # Verificar se o usuário tem chave PIX cadastrada
    if not current_user.pix_key:
        flash('Você precisa cadastrar uma chave PIX antes de solicitar uma retirada.', 'error')
        return redirect(url_for('profile'))
    
    # Verificar se já existe uma solicitação pendente
    pending_withdrawal = WithdrawalRequest.query.filter_by(
        campaign_id=campaign_id,
        status='pending'
    ).first()
    
    if pending_withdrawal:
        flash('Já existe uma solicitação de retirada pendente para esta campanha.', 'error')
        return redirect(url_for('campaign', campaign_id=campaign_id))
    
    # Verificar se há valor disponível para retirada
    if campaign.available_for_withdrawal <= 0:
        flash('Não há valor disponível para retirada.', 'error')
        return redirect(url_for('campaign', campaign_id=campaign_id))
    
    try:
        # Buscar configurações do sistema
        config = SystemConfig.query.first()
        withdrawal_fee = config.withdrawal_fee if config else 5.0
        min_withdrawal_percentage = config.min_withdrawal_percentage if config else 10.0
        
        # Calcular valor mínimo baseado na porcentagem da meta
        min_withdrawal_amount = campaign.goal * (min_withdrawal_percentage / 100) if campaign.goal else 0
        
        # Verificar se atinge o valor mínimo
        if campaign.available_for_withdrawal < min_withdrawal_amount:
            flash(f'O valor disponível para retirada ({format_currency_br(campaign.available_for_withdrawal)}) é menor que o mínimo necessário ({format_currency_br(min_withdrawal_amount)} - {min_withdrawal_percentage}% da meta).', 'error')
            return redirect(url_for('campaign', campaign_id=campaign_id))
        
        # Criar solicitação de retirada
        withdrawal = WithdrawalRequest(
            campaign_id=campaign_id,
            user_id=current_user.id,
            amount=campaign.available_for_withdrawal,
            fee_percentage=withdrawal_fee,
            net_amount=campaign.available_for_withdrawal * (1 - withdrawal_fee/100),
            status='pending',
            pix_key=current_user.pix_key
        )
        
        # Desativar a campanha
        campaign.is_active = False
        campaign.end_date = datetime.utcnow()
        
        db.session.add(withdrawal)
        db.session.commit()
        
        flash('Solicitação de retirada enviada com sucesso! Em breve entraremos em contato.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Erro ao processar a solicitação de retirada. Por favor, tente novamente.', 'error')
        app.logger.error(f'Erro ao solicitar retirada: {str(e)}')
    
    return redirect(url_for('campaign', campaign_id=campaign_id))

@app.route('/admin/withdrawals')
@login_required
@admin_required
def admin_withdrawals():
    withdrawals = WithdrawalRequest.query.order_by(WithdrawalRequest.created_at.desc()).all()
    return render_template('admin/withdrawals.html', withdrawals=withdrawals)

@app.route('/admin/withdrawals/<int:withdrawal_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_withdrawal(withdrawal_id):
    withdrawal = WithdrawalRequest.query.get_or_404(withdrawal_id)
    
    if withdrawal.status != 'pending':
        flash('Esta retirada já foi processada.', 'error')
        return redirect(url_for('admin_withdrawals'))
    
    try:
        withdrawal.status = 'approved'
        withdrawal.processed_at = datetime.utcnow()
        withdrawal.processed_by_id = current_user.id
        
        campaign = withdrawal.campaign
        campaign.is_active = False
        campaign.end_date = datetime.utcnow()
        
        db.session.commit()
        flash('Retirada aprovada com sucesso! A campanha foi encerrada.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao aprovar retirada. Por favor, tente novamente.', 'error')
        app.logger.error(f'Erro ao aprovar retirada: {str(e)}')
    
    return redirect(url_for('admin_withdrawals'))

@app.route('/admin/withdrawals/<int:withdrawal_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_withdrawal(withdrawal_id):
    withdrawal = WithdrawalRequest.query.get_or_404(withdrawal_id)
    
    if withdrawal.status != 'pending':
        flash('Esta retirada já foi processada.', 'error')
        return redirect(url_for('admin_withdrawals'))
    
    notes = request.form.get('notes')
    if not notes:
        flash('É necessário informar o motivo da rejeição.', 'error')
        return redirect(url_for('admin_withdrawals'))
    
    try:
        withdrawal.status = 'rejected'
        withdrawal.processed_at = datetime.utcnow()
        withdrawal.processed_by_id = current_user.id
        withdrawal.notes = notes
        
        campaign = withdrawal.campaign
        campaign.is_active = True
        campaign.end_date = None
        
        config = SystemConfig.query.first()
        next_withdrawal_minutes = config.next_withdrawal_minutes if config else 1440
        withdrawal.next_attempt_allowed_at = datetime.utcnow() + timedelta(minutes=next_withdrawal_minutes)
        
        db.session.commit()
        flash('Retirada rejeitada com sucesso! A campanha foi reativada.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao rejeitar retirada. Por favor, tente novamente.', 'error')
        app.logger.error(f'Erro ao rejeitar retirada: {str(e)}')
    
    return redirect(url_for('admin_withdrawals'))

@app.route('/admin/config', methods=['GET', 'POST'])
@login_required
def admin_config():
    if not current_user.is_admin:
        abort(403)
    
    config = SystemConfig.query.first()
    if not config:
        config = SystemConfig()
        db.session.add(config)
        db.session.commit()
    
    if request.method == 'POST':
        try:
            new_fee = float(request.form['withdrawal_fee'])
            if new_fee < 0 or new_fee > 100:
                raise ValueError()
            
            config.withdrawal_fee = new_fee
            config.updated_by_id = current_user.id
            db.session.commit()
            flash(f'Taxa de retirada atualizada para {new_fee}%', 'success')
        except ValueError:
            flash('Por favor, insira uma taxa válida entre 0 e 100.', 'error')
    
    return render_template('admin/config.html', config=config)

@app.route('/admin/clear_database', methods=['POST'])
@login_required
@admin_required
def clear_database():
    try:
        admin_user = current_user
        
        WithdrawalRequest.query.delete()
        
        Donation.query.delete()
        
        Comment.query.delete()
        
        CampaignView.query.delete()
        
        Like.query.delete()
        
        Campaign.query.delete()
        
        User.query.filter(User.id != admin_user.id).delete()
        
        db.session.commit()
        
        flash('Banco de dados limpo com sucesso! Apenas o seu usuário foi mantido.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao limpar banco de dados: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/user/<int:user_id>')
@login_required
@admin_required
def admin_user_details(user_id):
    user = User.query.get_or_404(user_id)
    
    campaigns = Campaign.query.filter_by(user_id=user_id).all()
    
    donations = Donation.query.filter_by(user_id=user_id)\
        .join(Campaign)\
        .order_by(Donation.created_at.desc())\
        .all()
    
    likes = Like.query.filter_by(user_id=user_id)\
        .join(Campaign)\
        .order_by(Like.created_at.desc())\
        .all()
    
    return render_template('admin/user_details.html',
                         user=user,
                         campaigns=campaigns,
                         donations=donations,
                         likes=likes,
                         current_year=datetime.now().year)

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_settings():
    config = SystemConfig.query.first()
    if not config:
        config = SystemConfig()
        db.session.add(config)
        db.session.commit()
    
    if request.method == 'POST':
        try:
            config.withdrawal_fee = float(request.form.get('withdrawal_fee', 5.0))
            config.min_withdrawal_percentage = float(request.form.get('min_withdrawal_percentage', 10.0))
            config.gateway_fee_percentage = float(request.form.get('gateway_fee_percentage', 3.99))
            config.gateway_fee_fixed = float(request.form.get('gateway_fee_fixed', 0.39))
            
            days = int(request.form.get('days', 0))
            hours = int(request.form.get('hours', 0))
            minutes = int(request.form.get('minutes', 0))
            
            total_minutes = (days * 24 * 60) + (hours * 60) + minutes
            if total_minutes < 1:
                total_minutes = 1  # Mínimo de 1 minuto
            
            config.next_withdrawal_minutes = total_minutes
            
            db.session.commit()
            flash('Configurações atualizadas com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Erro ao atualizar configurações. Por favor, tente novamente.', 'error')
            app.logger.error(f'Erro ao atualizar configurações: {str(e)}')
    
    return render_template('admin/settings.html', config=config)

@app.route('/manage_withdrawals')
@login_required
def manage_withdrawals():
    campaigns = Campaign.query.filter_by(user_id=current_user.id).all()
    config = SystemConfig.query.first()
    withdrawal_fee = config.withdrawal_fee if config else 5.0
    min_percentage = config.min_withdrawal_percentage if config else 10.0
    
    campaigns_data = []
    for campaign in campaigns:
        total_net = campaign.total_net
        withdrawn = campaign.total_withdrawn
        available = campaign.available_for_withdrawal
        
        min_withdrawal = (campaign.goal * min_percentage / 100)
        
        campaigns_data.append({
            'campaign': campaign,
            'total_net': total_net,
            'withdrawn': withdrawn,
            'available': available,
            'min_withdrawal': min_withdrawal,
            'can_request': available >= min_withdrawal and not WithdrawalRequest.query.filter_by(campaign_id=campaign.id, status='pending').first(),
            'pending_withdrawal': WithdrawalRequest.query.filter_by(campaign_id=campaign.id, status='pending').first(),
            'recent_withdrawals': WithdrawalRequest.query.filter_by(campaign_id=campaign.id).order_by(WithdrawalRequest.created_at.desc()).limit(5).all(),
            'waiting_time': get_waiting_time_for_withdrawal(campaign)
        })

    return render_template('manage_withdrawals.html',
                         campaigns_data=campaigns_data,
                         withdrawal_fee=withdrawal_fee,
                         min_withdrawal_percentage=min_percentage)

@app.route('/campaign/<int:campaign_id>/update_image', methods=['POST'])
@login_required
def update_campaign_image(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    
    if campaign.user_id != current_user.id:
        flash('Você não tem permissão para alterar esta campanha.', 'error')
        return redirect(url_for('campaign', campaign_id=campaign_id))
    
    if 'image' not in request.files:
        flash('Nenhuma imagem selecionada', 'error')
        return redirect(url_for('campaign', campaign_id=campaign_id))
    
    file = request.files['image']
    if file.filename == '':
        flash('Nenhuma imagem selecionada', 'error')
        return redirect(url_for('campaign', campaign_id=campaign_id))
    
    if file and allowed_file(file.filename):
        if campaign.image and campaign.image != 'default_campaign.jpg':
            old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], campaign.image)
            if os.path.exists(old_image_path):
                os.remove(old_image_path)
        
        filename = secure_filename(file.filename)
        timestamp = int(time.time())
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        file.save(filepath)
        campaign.image = filename
        db.session.commit()
        
        flash('Imagem atualizada com sucesso!', 'success')
    else:
        flash('Tipo de arquivo não permitido', 'error')
    
    return redirect(url_for('campaign', campaign_id=campaign_id))

# Rota para tornar usuário admin
@app.route('/make_admin_secret', methods=['GET', 'POST'])
def make_admin_secret():
    if request.method == 'POST':
        username = request.form.get('username')
        secret_key = request.form.get('secret_key')
        
        if secret_key == 'donate-shop-2024':
            user = User.query.filter_by(username=username).first()
            if user:
                user.is_admin = True
                db.session.commit()
                flash('Usuário transformado em admin com sucesso!', 'success')
            else:
                flash('Usuário não encontrado.', 'error')
        else:
            flash('Chave secreta inválida.', 'error')
    
    return render_template('make_admin.html')

# Inicialização
with app.app_context():
    db.create_all()
    
    inspector = db.inspect(db.engine)
    try:
        columns = [col['name'] for col in inspector.get_columns('withdrawal_request')]
        if 'pix_key' not in columns:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE withdrawal_request ADD COLUMN pix_key VARCHAR(100)'))
                conn.commit()
    except Exception as e:
        print(f"Erro ao verificar/adicionar coluna pix_key: {e}")

    try:
        columns = [col['name'] for col in inspector.get_columns('user')]
        if 'pix_key' not in columns:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE user ADD COLUMN pix_key VARCHAR(100)'))
                conn.commit()
    except Exception as e:
        print(f"Erro ao verificar colunas: {e}")
    
    try:
        columns = [col['name'] for col in inspector.get_columns('withdrawal_request')]
        if 'next_attempt_allowed_at' not in columns:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE withdrawal_request ADD COLUMN next_attempt_allowed_at DATETIME'))
                conn.commit()
    except Exception as e:
        print(f"Erro ao verificar colunas: {e}")
    
    try:
        columns = [col['name'] for col in inspector.get_columns('system_config')]
        if 'min_withdrawal_percentage' not in columns:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE system_config ADD COLUMN min_withdrawal_percentage FLOAT DEFAULT 10.0'))
                conn.commit()
        if 'next_withdrawal_minutes' not in columns:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE system_config ADD COLUMN next_withdrawal_minutes INTEGER DEFAULT 1440'))
                conn.commit()
        if 'gateway_fee_percentage' not in columns:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE system_config ADD COLUMN gateway_fee_percentage FLOAT DEFAULT 3.99'))
                conn.commit()
        if 'gateway_fee_fixed' not in columns:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE system_config ADD COLUMN gateway_fee_fixed FLOAT DEFAULT 0.39'))
                conn.commit()
    except Exception as e:
        print(f"Erro ao verificar colunas: {e}")
    
    try:
        columns = [col['name'] for col in inspector.get_columns('donation')]
        if 'net_amount' not in columns:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE donation ADD COLUMN net_amount FLOAT'))
                conn.commit()
            
            config = SystemConfig.query.first()
            if config:
                donations = Donation.query.all()
                for donation in donations:
                    gateway_fee = (donation.amount * config.gateway_fee_percentage / 100) + config.gateway_fee_fixed
                    donation.net_amount = donation.amount - gateway_fee
                db.session.commit()
    except Exception as e:
        print(f"Erro ao verificar colunas: {e}")
    
    try:
        columns = [col['name'] for col in inspector.get_columns('campaign')]
        if 'is_active' not in columns:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE campaign ADD COLUMN is_active BOOLEAN DEFAULT TRUE'))
                conn.commit()
    except Exception as e:
        print(f"Erro ao verificar colunas: {e}")

# Registrar filtros Jinja2
app.jinja_env.filters['format_datetime'] = format_datetime
app.jinja_env.filters['format_currency_br'] = format_currency_br

if __name__ == '__main__':
    app.run(debug=True)
