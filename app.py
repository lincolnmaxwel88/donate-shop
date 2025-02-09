# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from functools import wraps
import time
import stripe
from flask_mail import Mail, Message
from config import Config

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
app.config['CONTACT_EMAIL'] = 'your-contact-email@example.com'

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
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    is_blocked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    profile_image = db.Column(db.String(100))
    campaigns = db.relationship('Campaign', backref='creator', lazy=True)
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
    goal = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0)
    withdrawn_amount = db.Column(db.Float, default=0)
    end_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    image = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    allow_comments = db.Column(db.Boolean, default=True)
    views = db.Column(db.Integer, default=0)
    likes = db.relationship('Like', backref='campaign', lazy=True)
    donations = db.relationship('Donation', backref='campaign', lazy=True)
    comments = db.relationship('Comment', backref='campaign', lazy=True, cascade='all, delete-orphan')
    campaign_views = db.relationship('CampaignView', backref='campaign', lazy=True)
    # Relação com WithdrawalRequest
    withdrawals = db.relationship('WithdrawalRequest',
                                backref=db.backref('campaign', lazy=True),
                                lazy=True)

    @property
    def progress_percentage(self):
        if self.goal <= 0:
            return 0
        return min(100, (self.current_amount / self.goal) * 100)
    
    @property
    def days_remaining(self):
        if not self.end_date:
            return None
        delta = self.end_date - datetime.utcnow()
        return max(0, delta.days)
    
    @property
    def available_for_withdrawal(self):
        """Retorna o valor disponível para saque"""
        return max(0, self.current_amount - self.withdrawn_amount)

class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
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
    fee_percentage = db.Column(db.Float, nullable=False)  # Taxa aplicada no momento da solicitação
    net_amount = db.Column(db.Float, nullable=False)  # Valor após a dedução da taxa
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    processed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    notes = db.Column(db.Text)  # Para comentários do admin

class SystemConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    withdrawal_fee = db.Column(db.Float, nullable=False, default=5.0)  # Taxa padrão de 5%
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
        # Formata o número com 2 casas decimais
        value = float(value)
        # Separa a parte inteira da decimal
        int_part = int(value)
        decimal_part = int((value - int_part) * 100)
        
        # Formata a parte inteira com pontos a cada 3 dígitos
        str_int = str(int_part)
        groups = []
        while str_int:
            groups.insert(0, str_int[-3:])
            str_int = str_int[:-3]
        formatted_int = '.'.join(groups)
        
        # Junta tudo no formato R$ X.XXX,XX
        return f"R$ {formatted_int},{decimal_part:02d}"
    except:
        return "R$ 0,00"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

# Rotas
@app.route('/')
def index():
    campaigns = Campaign.query.order_by(Campaign.created_at.desc()).all()
    return render_template('index.html', campaigns=campaigns, current_year=datetime.now().year)

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
            # Criar o email
            msg = Message(
                subject=f'Contato do Site: {subject}',
                recipients=[app.config['CONTACT_EMAIL']],
                body=f'''
Nova mensagem de contato:

Nome: {name}
Email: {email}
Telefone: {phone}
Assunto: {subject}

Mensagem:
{message}
''')
            
            # Enviar o email
            mail.send(msg)
            
            flash('Sua mensagem foi enviada com sucesso! Entraremos em contato em breve.', 'success')
        except Exception as e:
            flash('Erro ao enviar mensagem. Por favor, tente novamente mais tarde.', 'error')
            print(f'Erro ao enviar email: {str(e)}')
        
        return redirect(url_for('contact'))
    
    return render_template('contact.html', current_year=datetime.now().year)

@app.route('/profile')
@login_required
def profile():
    # Estatísticas do usuário
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
    campaigns = Campaign.query.filter_by(user_id=current_user.id).order_by(Campaign.created_at.desc()).all()
    return render_template('my_campaigns.html', campaigns=campaigns, current_year=datetime.now().year)

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
            creator=current_user
        )
        
        # Handle image upload
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
    # Pegar as campanhas que o usuário curtiu
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
    # Estatísticas gerais
    total_users = User.query.count()
    total_campaigns = Campaign.query.count()
    total_donations = Donation.query.count()
    total_amount = db.session.query(db.func.sum(Donation.amount)).scalar() or 0
    
    # Lista de usuários
    users = User.query.order_by(User.username).all()
    
    # Últimas campanhas
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
    
    # Não permitir que um admin remova seus próprios privilégios
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
    
    # Não permitir bloquear um admin
    if user.is_admin:
        return jsonify({'success': False, 'message': 'Não é possível bloquear um administrador'})
    
    # Não permitir que um admin bloqueie a si mesmo
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
    
    # Registrar visualização
    if current_user.is_authenticated:
        # Pegar o IP do usuário
        ip_address = request.remote_addr
        
        # Verificar se já existe uma visualização por IP ou por usuário
        view = CampaignView.query.filter(
            CampaignView.campaign_id == campaign_id,
            db.or_(
                CampaignView.ip_address == ip_address,
                CampaignView.user_id == current_user.id
            )
        ).first()
        
        if not view:
            view = CampaignView(
                campaign_id=campaign_id,
                user_id=current_user.id,
                ip_address=ip_address
            )
            campaign.views += 1
            db.session.add(view)
            db.session.commit()
    
    # Obter a taxa de retirada das configurações
    config = SystemConfig.query.first()
    withdrawal_fee = config.withdrawal_fee if config else 5.0
    
    return render_template('campaign.html',
                         campaign=campaign,
                         donations=donations,
                         comments=comments,
                         withdrawal_fee=withdrawal_fee,
                         now=datetime.utcnow())

@app.route('/campaign/<int:campaign_id>/donate', methods=['POST'])
@login_required
def donate(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    
    # Pegar o valor e converter para o formato correto
    amount_str = request.form.get('amount', '0')
    try:
        # Remove qualquer caractere que não seja número ou vírgula
        amount_str = ''.join(c for c in amount_str if c.isdigit() or c == ',')
        # Converte vírgula para ponto
        amount = float(amount_str.replace(',', '.'))
    except ValueError:
        flash('Por favor, insira um valor válido.', 'error')
        return redirect(url_for('campaign', campaign_id=campaign_id))
    
    if not amount or amount <= 0:
        flash('Por favor, insira um valor válido.', 'error')
        return redirect(url_for('campaign', campaign_id=campaign_id))
    
    try:
        # Criar sessão de checkout do Stripe
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'brl',
                    'unit_amount': int(amount * 100),  # Stripe trabalha com centavos
                    'product_data': {
                        'name': f'Doação para: {campaign.title}',
                        'description': f'Campanha criada por {campaign.creator.username}',
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=url_for('donation_success', campaign_id=campaign_id, amount=amount, _external=True),
            cancel_url=url_for('donation_cancel', campaign_id=campaign_id, _external=True),
            metadata={
                'campaign_id': campaign_id,
                'user_id': current_user.id,
                'amount': amount
            }
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        app.logger.error(f"Erro Stripe: {str(e)}")
        flash('Erro ao processar pagamento. Por favor, tente novamente.', 'error')
        return redirect(url_for('campaign', campaign_id=campaign_id))

@app.route('/donation/success/<int:campaign_id>')
@login_required
def donation_success(campaign_id):
    amount = request.args.get('amount', type=float)
    campaign = Campaign.query.get_or_404(campaign_id)
    
    # Criar a doação
    donation = Donation(
        amount=amount,
        user_id=current_user.id,
        campaign_id=campaign_id
    )
    
    # Atualizar o valor arrecadado da campanha
    campaign.current_amount += amount
    
    db.session.add(donation)
    db.session.commit()
    
    flash('Doação realizada com sucesso! Obrigado pela sua contribuição.', 'success')
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
            payload, sig_header, 'seu_webhook_secret'  # Você precisará configurar isso no painel do Stripe
        )
    except ValueError as e:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        return 'Invalid signature', 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Processar o pagamento bem-sucedido
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
    
    # Verificar se o usuário já curtiu
    like = Like.query.filter_by(
        user_id=current_user.id,
        campaign_id=campaign_id
    ).first()
    
    if like:
        # Se já curtiu, remove o like
        db.session.delete(like)
        liked = False
    else:
        # Se não curtiu, adiciona o like
        like = Like(user_id=current_user.id, campaign_id=campaign_id)
        db.session.add(like)
        liked = True
    
    db.session.commit()
    
    # Contar o número total de likes
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

@app.route('/campaign/<int:campaign_id>/update_image', methods=['POST'])
@login_required
def update_campaign_image(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    
    if campaign.creator != current_user and not current_user.is_admin:
        abort(403)
    
    if 'image' not in request.files:
        flash('Nenhum arquivo selecionado', 'error')
        return redirect(url_for('campaign', campaign_id=campaign_id))
    
    file = request.files['image']
    if file.filename == '':
        flash('Nenhum arquivo selecionado', 'error')
        return redirect(url_for('campaign', campaign_id=campaign_id))
    
    if file and allowed_file(file.filename):
        # Remove a imagem antiga se existir
        if campaign.image and campaign.image != 'default_campaign.jpg':
            old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], campaign.image)
            if os.path.exists(old_image_path):
                os.remove(old_image_path)
        
        # Salva a nova imagem
        filename = secure_filename(file.filename)
        timestamp = int(time.time())
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        file.save(filepath)
        
        campaign.image = filename
        db.session.commit()
        
        flash('Imagem atualizada com sucesso!', 'success')
        return redirect(url_for('campaign', campaign_id=campaign_id))
    
    flash('Tipo de arquivo não permitido', 'error')
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
        # Gerar um nome único para o arquivo
        filename = secure_filename(f"{current_user.username}_{int(time.time())}_{photo.filename}")
        # Criar pasta profiles se não existir
        profiles_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'profiles')
        if not os.path.exists(profiles_folder):
            os.makedirs(profiles_folder)
        
        # Salvar a foto na pasta profiles
        photo_path = os.path.join(profiles_folder, filename)
        photo.save(photo_path)
        
        # Atualizar o perfil do usuário com o caminho relativo usando forward slash
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
    # Verificar se o usuário é o dono da campanha ou admin
    if current_user.id != campaign.user_id and not current_user.is_admin:
        abort(403)
    
    donations = Donation.query.filter_by(campaign_id=campaign_id)\
        .order_by(Donation.created_at.desc()).all()
    
    return render_template('donation_history.html', 
                         campaign=campaign, 
                         donations=donations,
                         current_year=datetime.now().year)

@app.route('/campaign/<int:campaign_id>/request-withdrawal', methods=['POST'])
@login_required
def request_withdrawal(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    
    # Verificar se o usuário é o dono da campanha
    if campaign.user_id != current_user.id:
        abort(403)
    
    # Verificar se já existe alguma solicitação de retirada (independente do status)
    existing_withdrawal = WithdrawalRequest.query.filter_by(campaign_id=campaign_id).first()
    if existing_withdrawal:
        flash('Esta campanha já possui uma solicitação de retirada. Não é possível solicitar mais de uma vez.', 'warning')
        return redirect(url_for('campaign', campaign_id=campaign_id))
    
    # Verificar se há valor disponível para retirada
    if campaign.available_for_withdrawal <= 0:
        flash('Não há valor disponível para retirada.', 'warning')
        return redirect(url_for('campaign', campaign_id=campaign_id))
    
    # Obter a taxa de retirada das configurações
    config = SystemConfig.query.first()
    fee_percentage = config.withdrawal_fee if config else 5.0
    
    # Calcular valores
    amount = campaign.available_for_withdrawal
    net_amount = amount * (1 - fee_percentage/100)
    
    # Criar a solicitação de retirada
    withdrawal = WithdrawalRequest(
        campaign_id=campaign_id,
        user_id=current_user.id,
        amount=amount,
        fee_percentage=fee_percentage,
        net_amount=net_amount
    )
    
    # Encerrar a campanha
    campaign.end_date = datetime.utcnow()
    
    db.session.add(withdrawal)
    db.session.commit()
    
    flash('Sua solicitação de retirada foi enviada! A campanha foi encerrada e não receberá mais doações.', 'success')
    return redirect(url_for('campaign', campaign_id=campaign_id))

@app.route('/admin/withdrawals')
@login_required
@admin_required
def admin_withdrawals():
    withdrawals = WithdrawalRequest.query.order_by(WithdrawalRequest.created_at.desc()).all()
    return render_template('admin/withdrawals.html', withdrawals=withdrawals)

@app.route('/admin/withdrawals/approve/<int:withdrawal_id>', methods=['POST'])
@login_required
@admin_required
def approve_withdrawal(withdrawal_id):
    withdrawal = WithdrawalRequest.query.get_or_404(withdrawal_id)
    if withdrawal.status != 'pending':
        flash('Esta solicitação já foi processada.', 'warning')
        return redirect(url_for('admin_withdrawals'))
    
    withdrawal.status = 'approved'
    withdrawal.processed_at = datetime.utcnow()
    withdrawal.processed_by_id = current_user.id
    db.session.commit()
    
    flash('Solicitação de retirada aprovada com sucesso!', 'success')
    return redirect(url_for('admin_withdrawals'))

@app.route('/admin/withdrawals/reject/<int:withdrawal_id>', methods=['POST'])
@login_required
@admin_required
def reject_withdrawal(withdrawal_id):
    withdrawal = WithdrawalRequest.query.get_or_404(withdrawal_id)
    if withdrawal.status != 'pending':
        flash('Esta solicitação já foi processada.', 'warning')
        return redirect(url_for('admin_withdrawals'))
    
    # Devolver o valor para o saldo disponível
    campaign = withdrawal.campaign
    campaign.withdrawn_amount -= withdrawal.amount
    
    withdrawal.status = 'rejected'
    withdrawal.processed_at = datetime.utcnow()
    withdrawal.processed_by_id = current_user.id
    db.session.commit()
    
    flash('Solicitação de retirada rejeitada com sucesso!', 'success')
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
        # Usar o usuário atual (que já sabemos que é admin devido ao @admin_required)
        admin_user = current_user
        
        # Excluir todas as solicitações de retirada
        WithdrawalRequest.query.delete()
        
        # Excluir todas as doações
        Donation.query.delete()
        
        # Excluir todos os comentários
        Comment.query.delete()
        
        # Excluir todas as visualizações
        CampaignView.query.delete()
        
        # Excluir todas as curtidas
        Like.query.delete()
        
        # Excluir todas as campanhas
        Campaign.query.delete()
        
        # Excluir todos os usuários exceto o admin atual
        User.query.filter(User.id != admin_user.id).delete()
        
        db.session.commit()
        flash('Banco de dados limpo com sucesso! Apenas o seu usuário foi mantido.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao limpar banco de dados: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard'))

# Registrar filtros Jinja2
app.jinja_env.filters['format_datetime'] = format_datetime
app.jinja_env.filters['format_currency_br'] = format_currency_br

# Inicialização
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Criar todas as tabelas
    app.run(debug=True)
