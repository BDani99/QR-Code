from flask import Flask,jsonify,request,session
from flask_bcrypt import Bcrypt
from flask_cors import CORS,cross_origin
from models import db,User,Ticket,Event
from functools import wraps
from uuid import uuid4
from datetime import datetime
import os
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_jwt_extended import JWTManager
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required


app = Flask(__name__)
admin=Admin()


app.config['SECRET_KEY'] = 'QR-CODE'
app.config['JWT_SECRET_KEY']=os.environ.get('JWT_SECRET','sample key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///qrcodedb.db'


admin.add_view(ModelView(User,db.session))
admin.add_view(ModelView(Ticket,db.session))
admin.add_view(ModelView(Event,db.session))

SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = True

jwt = JWTManager(app)
bcrypt=Bcrypt(app)
CORS(app, supports_credentials=True)
db.init_app(app)
admin.init_app(app)

with app.app_context():
    db.create_all()

# @app.route("/token", methods=["POST"])
# def create_token():
#     email = request.json.get("email", None)
#     password = request.json.get("password", None)
#     if email != "test" or password != "test":
#         return jsonify({"msg": "Bad username or password"}), 401

#     access_token = create_access_token(identity=email)
#     return jsonify(access_token=access_token)


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
    access_token = create_access_token(identity=email)
  
    return jsonify({
        "id": user.id,
        "email": user.email,
        "token":access_token
    })


@app.route("/@me")
def get_current_user():
    user_id=session.get("user_id")

    if not user_id:
        return jsonify({"error": "Anauthorised"}), 401
    
    user = User.query.filter_by(id=str(user_id)).first()

    if not user:
        return jsonify({"error": "User not found"}), 404
    
    user = User.query.filter_by(id=user_id).first()
    return jsonify({
        "id": user.id,
        "email": user.email,
        "name":user.name,
        "dateOfBirth":user.dateOfBirth,
        "address":user.address,
        "placeOfBirth":user.placeOfBirth,
        "isAdmin":user.admin
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



@app.route("/logout" ,methods=["POST"])
def logout_user():
    session.pop("user_id")
    return "200"

@app.route("/events")
@jwt_required()
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

@app.route("/ticket/<int:ticket_id>")
def get_single_ticket(ticket_id):
    ticket = Ticket.query.get(ticket_id)

    if not ticket:
        return jsonify({"message": "Event not found"}), 404

    ticket_data = {
        "id": ticket.id,
        "name": ticket.event.name,
        "event_date": ticket.event.dateOfEvent,
        "event_location": ticket.event.location,
        "event_image": ticket.event.image,
        "event_price": ticket.event.price,
        "user_name":ticket.user.name,
        "dateOfBuyig": ticket.dateOfBuyig,
        "user_name":ticket.user.name,
        "qrcode":ticket.qrcode

    }

    return jsonify({"ticket": ticket_data})


@app.route("/tickets", methods=["GET"])
def get_tickets():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_tickets = Ticket.query.filter_by(user_id=user_id).all()

    tickets_data = []
    for ticket in user_tickets:
        tickets_data.append({
            "ticket_id": ticket.id,
            "event_name": ticket.event.name,
            "event_date": ticket.event.dateOfEvent,
            "event_location": ticket.event.location,
            "qrcode": ticket.qrcode,
            "event_image":ticket.event.image,
            "dateOfBuyig": ticket.dateOfBuyig,
            "event_price": ticket.event.price
        })

    return jsonify({"tickets": tickets_data}), 200


if __name__=="__main__":
    app.run(debug=True)