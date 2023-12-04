from flask_sqlalchemy import SQLAlchemy
from uuid import uuid4

db=SQLAlchemy()

def get_uuid():
    return uuid4().hex

class User(db.Model):
    __tablename__="users"
    id=db.Column(db.String(11),primary_key=True,unique=True,default=get_uuid)
    email=db.Column(db.String(150),unique=True)
    password=db.Column(db.Text,nullable=False)
    name=db.Column(db.String(50))
    dateOfBirth=db.Column(db.String(10))
    address=db.Column(db.String(100))
    placeOfBirth=db.Column(db.String(100))
    admin=db.Column(db.Boolean,default=False)
    tickets = db.relationship('Ticket', backref='user_ref')

class Ticket(db.Model):
    __tablename__="tickets"
    id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    qrcode=db.Column(db.String(20))
    dateOfBuyig=db.Column(db.String(10))
    numberofTickets=db.Column(db.Integer)
    isScanned=db.Column(db.Integer,default=False)
    user_id = db.Column(db.String(11), db.ForeignKey('users.id'), nullable=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    user = db.relationship('User', backref='ticket_ref')
    event = db.relationship('Event', backref='ticket')
    

class Event(db.Model):
    __tablename__="events"
    id=db.Column(db.Integer,primary_key=True,unique=True,)
    name=db.Column(db.String(50))
    dateOfEvent=db.Column(db.String(10))
    location=db.Column(db.String(30))
    price=db.Column(db.Integer)
    category=db.Column(db.String(30))
    description=db.Column(db.String(50))
    image=db.Column(db.Text)    
    tickets = db.relationship('Ticket', backref='event_ref')

