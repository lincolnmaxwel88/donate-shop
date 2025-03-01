from app import app, db, User, Campaign, Comment, Like, SystemConfig
import json
from datetime import datetime

def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def parse_datetime(date_str):
    if date_str is None:
        return None
    try:
        return datetime.fromisoformat(date_str)
    except (TypeError, ValueError):
        return None

def export_data():
    with app.app_context():
        data = {
            'users': [user.__dict__ for user in User.query.all()],
            'campaigns': [campaign.__dict__ for campaign in Campaign.query.all()],
            'comments': [comment.__dict__ for comment in Comment.query.all()],
            'likes': [like.__dict__ for like in Like.query.all()],
            'system_config': [config.__dict__ for config in SystemConfig.query.all()]
        }
        
        # Remover atributos SQLAlchemy
        for category in data.values():
            for item in category:
                item.pop('_sa_instance_state', None)
        
        with open('database_backup.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, default=serialize_datetime, ensure_ascii=False, indent=2)
        print("Dados exportados com sucesso!")

def import_data():
    with app.app_context():
        # Criar todas as tabelas
        db.create_all()
        
        with open('database_backup.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Converter datas em cada objeto
        datetime_fields = ['created_at', 'updated_at', 'closed_at', 'last_login']
        
        for category in data.values():
            for item in category:
                for field in datetime_fields:
                    if field in item and item[field]:
                        item[field] = parse_datetime(item[field])
        
        # Importar usuários primeiro
        for user_data in data['users']:
            user = User()
            for key, value in user_data.items():
                setattr(user, key, value)
            db.session.add(user)
        db.session.commit()
        print("Usuários importados!")
        
        # Importar campanhas
        for campaign_data in data['campaigns']:
            campaign = Campaign()
            for key, value in campaign_data.items():
                setattr(campaign, key, value)
            db.session.add(campaign)
        db.session.commit()
        print("Campanhas importadas!")
        
        # Importar comentários
        for comment_data in data['comments']:
            comment = Comment()
            for key, value in comment_data.items():
                setattr(comment, key, value)
            db.session.add(comment)
        db.session.commit()
        print("Comentários importados!")
        
        # Importar likes
        for like_data in data['likes']:
            like = Like()
            for key, value in like_data.items():
                setattr(like, key, value)
            db.session.add(like)
        db.session.commit()
        print("Likes importados!")
        
        # Importar configurações do sistema
        for config_data in data['system_config']:
            config = SystemConfig()
            for key, value in config_data.items():
                setattr(config, key, value)
            db.session.add(config)
        db.session.commit()
        print("Configurações do sistema importadas!")
        
        print("Todos os dados foram importados com sucesso!")

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2 or sys.argv[1] not in ['export', 'import']:
        print("Uso: python migrate_data.py [export|import]")
        sys.exit(1)
    
    if sys.argv[1] == 'export':
        export_data()
    else:
        import_data()
