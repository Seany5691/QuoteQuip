from app import app, db
from models import Quote, Invoice

def migrate_database():
    with app.app_context():
        # Drop existing tables
        db.drop_all()
        
        # Create tables with new schema
        db.create_all()
        
        print("Database migrated successfully!")

if __name__ == '__main__':
    migrate_database()
