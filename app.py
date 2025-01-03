from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from flask_cors import CORS  # Import CORS


app = Flask(__name__)

# Enable CORS
CORS(app)  # This will enable CORS for all routes by default


# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///calendar_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "your_secret_key_here"

db = SQLAlchemy(app)

# Models
class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=True)
    linkedin_profile = db.Column(db.String(200), nullable=True)
    emails = db.Column(db.String(500), nullable=True)
    phone_numbers = db.Column(db.String(500), nullable=True)
    comments = db.Column(db.Text, nullable=True)
    communication_periodicity = db.Column(db.Integer, default=14)

class CommunicationMethod(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    sequence = db.Column(db.Integer, nullable=False)
    mandatory_flag = db.Column(db.Boolean, default=False)

class Communication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    method_id = db.Column(db.Integer, db.ForeignKey('communication_method.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    notes = db.Column(db.Text, nullable=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    role = db.Column(db.String(50), default='user')
    password_hash = db.Column(db.String(128), nullable=False)

# Initialize the database
with app.app_context():
    db.create_all()


# Routes

# Authentication Routes
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    hashed_password = generate_password_hash(data['password'])
    new_user = User(
        name=data['name'],
        email=data['email'],
        role=data.get('role', 'user'),
        password_hash=hashed_password
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    role = user.role if user else 'guest'  # Default role to guest if user not found
    if user and check_password_hash(user.password_hash, data['password']):
        # token = jwt.encode(
        #     {"user_id": user.id, "exp": datetime.utcnow() + timedelta(hours=24)},
        #     app.secret_key,
        #     algorithm="HS256"
        # )
        token = jwt.encode({"user_id": user.id}, app.secret_key, algorithm="HS256")
        return jsonify({"token": token, "role": role}), 200
    return jsonify({"message": "Invalid credentials"}), 401

# Company Management Routes
@app.route('/companies', methods=['GET'])
def get_companies():
    companies = Company.query.all()
    return jsonify([{
        "id": company.id,
        "name": company.name,
        "location": company.location,
        "linkedin_profile": company.linkedin_profile,
        "emails": company.emails,
        "phone_numbers": company.phone_numbers,
        "comments": company.comments,
        "communication_periodicity": company.communication_periodicity
    } for company in companies])

@app.route('/companies', methods=['POST'])
def add_company():
    data = request.json
    new_company = Company(
        name=data['name'],
        location=data.get('location'),
        linkedin_profile=data.get('linkedin_profile'),
        emails=data.get('emails', ''),
        phone_numbers=data.get('phone_numbers', ''),
        comments=data.get('comments', ''),
        communication_periodicity=data.get('communication_periodicity', 14)
    )
    db.session.add(new_company)
    db.session.commit()
    return jsonify({"message": "Company added successfully", "id": new_company.id}), 201

@app.route('/companies/<int:id>', methods=['PATCH'])
def edit_company(id):
    company = Company.query.get_or_404(id)
    data = request.json
    company.name = data.get('name', company.name)
    company.location = data.get('location', company.location)
    company.linkedin_profile = data.get('linkedin_profile', company.linkedin_profile)
    company.emails = data.get('emails', company.emails)
    company.phone_numbers = data.get('phone_numbers', company.phone_numbers)
    company.comments = data.get('comments', company.comments)
    company.communication_periodicity = data.get('communication_periodicity', company.communication_periodicity)
    db.session.commit()
    return jsonify({"message": "Company updated successfully"})

@app.route('/companies/<int:id>', methods=['DELETE'])
def delete_company(id):
    company = Company.query.get_or_404(id)
    db.session.delete(company)
    db.session.commit()
    return jsonify({"message": "Company deleted successfully"})

# Communication Management Routes
@app.route('/communications', methods=['POST'])
def log_communication():
    data = request.json
    new_communication = Communication(
        company_id=data['company_id'],
        method_id=data['method_id'],
        date=datetime.strptime(data['date'], "%Y-%m-%d"),
        notes=data.get('notes', '')
    )
    db.session.add(new_communication)
    db.session.commit()
    return jsonify({"message": "Communication logged successfully", "id": new_communication.id}), 201

@app.route('/communications', methods=['GET'])
def get_communications():
    company_id = request.args.get('company_id')
    if company_id:
        communications = Communication.query.filter_by(company_id=company_id).all()
    else:
        communications = Communication.query.all()
    return jsonify([{
        "id": comm.id,
        "company_id": comm.company_id,
        "method_id": comm.method_id,
        "date": comm.date.isoformat(),
        "notes": comm.notes
    } for comm in communications])

if __name__ == "__main__":
    app.run(debug=True, host='localhost')
