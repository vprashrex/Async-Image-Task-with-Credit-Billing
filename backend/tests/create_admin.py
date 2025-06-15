from sqlalchemy.orm import sessionmaker
from app.utils.auth import get_password_hash
from app.database import engine
from app.models.user import User

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()

def create_admin_user():
    # Check if admin already exists
    existing_admin = session.query(User).filter(User.username == 'admin').first()
    
    if existing_admin:
        print("Admin user already exists!")
        return
    
    # Create admin user
    admin_user = User(
        email='admin@virtualspacetech.com',
        username='admin',
        hashed_password=get_password_hash('admin123'),  # Change this password
        is_active=True,
        is_admin=True,
        credits=1000
    )
    
    session.add(admin_user)
    session.commit()
    print("Admin user created successfully!")

if __name__ == "__main__":
    create_admin_user()
    session.close()