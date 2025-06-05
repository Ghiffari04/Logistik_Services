from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///add_event.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

ADD_EVENT_SERVICE = "http://add_event_service:5007"

db = SQLAlchemy(app)

class Event(db.Model):
    event_id = db.Column(db.Integer, primary_key=True)
    nama_event = db.Column(db.String(255), nullable=False)
    deskripsi = db.Column(db.String(1000))
    tanggal_mulai = db.Column(db.Date, nullable=False)
    tanggal_selesai = db.Column(db.Date, nullable=False)
    status_approval = db.Column(db.String(50), default='Pending')

with app.app_context():
    db.create_all()

@app.route('/api/events', methods=['POST'])
def add_event():
    try:
        data = request.json
        required_fields = ['nama_event', 'deskripsi', 'tanggal_mulai', 'tanggal_selesai']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400

        # Gunakan fromisoformat untuk parsing ISO datetime string
        tanggal_mulai = datetime.fromisoformat(data['tanggal_mulai']).date()
        tanggal_selesai = datetime.fromisoformat(data['tanggal_selesai']).date()

        new_event = Event(
            event_id=int(datetime.now().timestamp()),
            nama_event=data['nama_event'],
            deskripsi=data['deskripsi'],
            tanggal_mulai=tanggal_mulai,
            tanggal_selesai=tanggal_selesai,
            status_approval='Approved'
        )
        db.session.add(new_event)
        db.session.commit()

        return jsonify({'message': 'Event created successfully', 'event_id': new_event.event_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/events', methods=['GET'])
def get_events():
    try:
        events = Event.query.all()
        event_list = [
            {
                'event_id': e.event_id,
                'nama_event': e.nama_event,
                'deskripsi': e.deskripsi,
                'tanggal_mulai': e.tanggal_mulai.isoformat(),
                'tanggal_selesai': e.tanggal_selesai.isoformat(),
                'status_approval': e.status_approval
            }
            for e in events
        ]
        return jsonify(event_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5007, debug=True)
