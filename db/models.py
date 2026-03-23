from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum, UniqueConstraint
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,relationship,declarative_base
from datetime import datetime
import os
import enum
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Integrations(enum.IntEnum):
    GMAIL = 1
    CALENDER = 2
    DOCS = 3
    DRIVE = 4
    MEET = 5
    SHEETS = 6
    TASKS = 7
    


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    google_id = Column(String, unique=True, nullable=False)
    joined_at = Column(DateTime, default=datetime.now())
    is_active = Column(Boolean, default=True)
    is_admin= Column(Boolean, default=False)
    thread_id = Column(String, nullable=True)  # OpenAI thread ID for conversation
    
    # Relationship with Profile
    profile= relationship("Profile", uselist=False, back_populates="user", cascade="all, delete-orphan")
    
    # Relationship with Channels
    channels = relationship("Channel", back_populates="user", cascade="all, delete-orphan")
    

class Profile(Base):
    __tablename__= "profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    name = Column(String, nullable=False)
    profile_picture = Column(String, default="https://via.placeholder.com/150", nullable=True)
    age = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())

    # Relationship with User
    user = relationship("User", back_populates="profile")


class APICredentials(Base):
    __tablename__ = "api_credentials"
    
    id = Column(Integer, primary_key=True)
    key_1 = Column(String(255), nullable=True)
    key_2 = Column(String(255), nullable=True)
    key_3 = Column(String(255), nullable=True)
    key_4 = Column(String(255), nullable=True)
    key_5 = Column(String(255), nullable=True)
    key_6 = Column(String(255), nullable=True)
    
    # Relationship with Channel
    channels = relationship("Channel", back_populates="credentials")
    
    def __str__(self):
        return "xyz"


class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True)
    channel_type = Column(Enum(Integrations), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    credentials_id = Column(Integer, ForeignKey("api_credentials.id", ondelete="CASCADE"), nullable=True, unique=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationship with APICredentials
    credentials = relationship("APICredentials", back_populates="channels")
    # Relationship with User
    user = relationship("User", back_populates="channels")
    
    # Unique constraint for user_id and channel_type combination
    __table_args__ = (UniqueConstraint('user_id', 'channel_type', name='unique_user_channel'),)

    
    def __str__(self):
        return 'xyz'