from flask import Flask,jsonify,request,session,make_response
from flask_bcrypt import Bcrypt
from flask_cors import CORS,cross_origin
from models import db,User,Ticket,Event
from functools import wraps
from uuid import uuid4
from datetime import datetime

app = Flask(__name__)

app.config['SECRET_KEY'] = 'QR-CODE'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///qrcodedb.db'

SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = True

bcrypt=Bcrypt(app)
CORS(app, supports_credentials=True)
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/@me")
def get_current_user():
    user_id=session.get("user_id")

    if not user_id:
        return jsonify({"error": "Anauthorised"}), 401

    user = User.query.filter_by(id=user_id).first()
    return jsonify({
        "id": user.id,
        "email": user.email,
        "name":user.name,
        "dateOfBirth":user.dateOfBirth,
        "address":user.address,
        "placeOfBirth":user.placeOfBirth
    })

@app.route('/buying', methods=['POST'])
def purchase_tickets():
    event_id=request.json["event_id"]
    user_id=request.json["user_id"]
    numberofTickets=request.json["numberofTickets"]
    dateOfBuyig = request.json["dateOfBuyig"]
    qrcode=request.json["qrcode"]

    event =Event.query.get(event_id)
    user=User.query.get(user_id)

    if not event or user:
        return jsonify({"message":"Event or user not found"}), 404
    
    for _ in range(numberofTickets):
        unique_qrcode = str(uuid4())
        ticket = Ticket(
        event_id=event_id,
        user_id=user_id,
        qrcode=unique_qrcode,  
        dateOfBuyig=dateOfBuyig,
        numberofTickets=numberofTickets
    )
        db.session.add(ticket)

    db.session.commit()

    session["user_id"]=ticket.user_id

    return jsonify({
        "event_id": ticket.event_id,
        "user_id":ticket.user_id,
        "qrcode": ticket.qrcode,
        "dateOfBuyig": ticket.dateOfBuyig
    }), 200

@app.route("/register", methods=["POST"])
def signup():
    email = request.json["email"]
    password = request.json["password"]
    name=request.json["name"]
    dateOfBirth = request.json["dateOfBirth"]
    address = request.json["address"]
    placeOfBirth = request.json["placeOfBirth"]

    user_exist=User.query.filter_by(email=email).first() is not None

    if user_exist:
        return jsonify({"error":"A felhasználó már létezik"}),409
    
    hashed_password=bcrypt.generate_password_hash(password)
    new_user =User(
        email=email,
        password=hashed_password,
        name=name,
        dateOfBirth=dateOfBirth,
        address=address,
        placeOfBirth=placeOfBirth
        )
    db.session.add(new_user)
    db.session.commit()

    session["user_id"]=new_user.id
    
    return jsonify({
        "id": new_user.id,
        "email": new_user.email,
        "name": new_user.name,
        "dateOfBirth": new_user.dateOfBirth,
        "address": new_user.address,
        "pleaceOfBirth": new_user.placeOfBirth
    })

@app.route("/login", methods=["POST"])
def login_user():
    email = request.json["email"]
    password = request.json["password"]
  
    user = User.query.filter_by(email=email).first()
  
    if user is None:
        return jsonify({"error": "Rossz felhasználónév vagy jelszó"}), 401
  
    if not bcrypt.check_password_hash(user.password, password):
        return jsonify({"error": "Rossz felhasználónév vagy jelszó"}), 401
      
    session["user_id"] = user.id
  
    return jsonify({
        "id": user.id,
        "email": user.email
    })

@app.route("/logout" ,methods=["POST"])
def logout_user():
    session.pop("user_id")
    return "200"

@app.route("/events")
def get_event():
    events = Event.query.all()

    event_list = []
    for event in events:
        event_dict = {
            "id":event.id,
            "name": event.name,
            "dateOfEvent": event.dateOfEvent,
            "location": event.location,
            "category": event.category,
            "description": event.description,
            "image": event.image,
            "price": event.price,

        }
        event_list.append(event_dict)

    return jsonify({"events": event_list})

@app.route("/events/<int:event_id>")
def get_single_event(event_id):
    event = Event.query.get(event_id)

    if not event:
        return jsonify({"message": "Event not found"}), 404

    event_data = {
        "id": event.id,
        "name": event.name,
        "dateOfEvent": event.dateOfEvent,
        "location": event.location,
        "category": event.category,
        "description": event.description,
        "image": event.image,
        "price": event.price,
    }

    return jsonify({"event": event_data})

@app.route("/buying/<int:event_id>")
def get_single_buying_event(event_id):
    event = Event.query.get(event_id)

    if not event:
        return jsonify({"message": "Event not found"}), 404

    event_data = {
        "id": event.id,
        "name": event.name,
        "dateOfEvent": event.dateOfEvent,
        "location": event.location,
        "price": event.price,
    }

    return jsonify({"event": event_data})

if __name__=="__main__":
    app.run(debug=True)