# models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    name = Column(String)
    email = Column(String)
    password_hash = Column(String)
    is_admin = Column(Boolean, default=False)

    campaigns = relationship("Campaign", back_populates="user", cascade="all, delete-orphan")
    sender_config = relationship("SenderConfig", uselist=False, back_populates="user")

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    service = Column(String)
    date_created = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    industries = Column(String)
    locations = Column(String) 
    platforms = Column(String) 

    user = relationship("User", back_populates="campaigns")
    leads = relationship("Lead", back_populates="campaign", cascade="all, delete-orphan")
    sender_config = relationship("SenderConfig", uselist=False, back_populates="campaign")

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    platform_source = Column(String)
    profile_link = Column(String)
    website = Column(String)
    state = Column(String)
    industry = Column(String)
    profile_description = Column(Text)
    email_subject = Column(String)
    generated_email = Column(Text)
    email_html = Column(Text)
    delivery_status = Column(String)
    opened = Column(Boolean, default=False)
    reply_text = Column(Text)
    reply_sentiment = Column(String)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))

    campaign = relationship("Campaign", back_populates="leads")

class SenderConfig(Base):
    __tablename__ = "sender_configs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sender_name = Column(String)
    sender_email = Column(String)
    company_name = Column(String)
    website = Column(String)
    phone = Column(String)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))

    user = relationship("User", back_populates="sender_config")
    campaign = relationship("Campaign", back_populates="sender_config")

class EmailContent(Base):
    __tablename__ = "email_contents"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    subject = Column(Text)
    body = Column(Text)
    html = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
