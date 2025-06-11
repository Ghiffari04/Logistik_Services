from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import time
import os
import requests
import logging

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///add_event.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Event(db.Model):
    event_id = db.Column(db.Integer, primary_key=True)
    nama_event = db.Column(db.String(255), nullable=False)
    deskripsi = db.Column(db.String(1000))
    tanggal_mulai = db.Column(db.Date, nullable=False)
    tanggal_selesai = db.Column(db.Date, nullable=False)
    status_approval = db.Column(db.String(50), default='Approved')

with app.app_context():
    db.create_all()
    
    # Add test events if database is empty
    if Event.query.count() == 0:
        test_events = [
            {
                'nama_event': 'Workshop Python',
                'deskripsi': 'Workshop pemrograman Python untuk pemula',
                'tanggal_mulai': datetime.now().date(),
                'tanggal_selesai': (datetime.now() + timedelta(days=1)).date()
            },
            {
                'nama_event': 'Seminar AI',
                'deskripsi': 'Seminar tentang Artificial Intelligence',
                'tanggal_mulai': (datetime.now() + timedelta(days=2)).date(),
                'tanggal_selesai': (datetime.now() + timedelta(days=3)).date()
            },
            {
                'nama_event': 'Hackathon Tel-U',
                'deskripsi': 'Hackathon tahunan Telkom University',
                'tanggal_mulai': (datetime.now() + timedelta(days=5)).date(),
                'tanggal_selesai': (datetime.now() + timedelta(days=7)).date()
            }
        ]
        
        for event_data in test_events:
            time.sleep(1)  # Add 1 second delay between events to ensure unique timestamps
            event = Event(
                event_id=int(datetime.now().timestamp()),
                nama_event=event_data['nama_event'],
                deskripsi=event_data['deskripsi'],
                tanggal_mulai=event_data['tanggal_mulai'],
                tanggal_selesai=event_data['tanggal_selesai'],
                status_approval='Approved'
            )
            db.session.add(event)
        
        db.session.commit()
        print("Test events created successfully!")

@app.route('/api/events', methods=['POST'])
def add_event():
    try:
        data = request.json
        required_fields = ['nama_event', 'deskripsi', 'tanggal_mulai', 'tanggal_selesai']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400

        tanggal_mulai = datetime.strptime(data['tanggal_mulai'], '%Y-%m-%d').date()
        tanggal_selesai = datetime.strptime(data['tanggal_selesai'], '%Y-%m-%d').date()

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

@app.route('/api/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    try:
        event = Event.query.get(event_id)
        if not event:
            return jsonify({'error': 'Event not found'}), 404
            
        return jsonify({
            'event_id': event.event_id,
            'nama_event': event.nama_event,
            'deskripsi': event.deskripsi,
            'tanggal_mulai': event.tanggal_mulai.isoformat(),
            'tanggal_selesai': event.tanggal_selesai.isoformat(),
            'status_approval': event.status_approval
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/approved-events', methods=['GET'])
def get_approved_events():
    try:
        response = requests.get(f"{ADD_EVENT_SERVICE}/api/events")
        response.raise_for_status()
        all_events = response.json()
        approved_events = [event for event in all_events if event.get('status_approval') == 'Approved']
        return jsonify(approved_events)
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Service error: {str(e)}'}), 500

@app.route('/api/bookings', methods=['GET'])
def get_all_bookings():
    bookings = Booking.query.all()
    # Fetch all events and rooms once (optional optimization)
    try:
        events_resp = requests.get(f"{ADD_EVENT_SERVICE}/api/events", timeout=2)
        events_map = {e['event_id']: e['nama_event'] for e in events_resp.json()} if events_resp.status_code == 200 else {}
    except Exception as e:
        logging.error(f"Failed to fetch events: {e}")
        events_map = {}
    try:
        rooms_resp = requests.get(f"{ROOM_AVAILABILITY_SERVICE}/rooms", timeout=2)
        rooms_map = {r['room_id']: r['nama_ruangan'] for r in rooms_resp.json()} if rooms_resp.status_code == 200 else {}
    except Exception as e:
        logging.error(f"Failed to fetch rooms: {e}")
        rooms_map = {}

    results = []
    for booking in bookings:
        nama_event = events_map.get(booking.event_id, '-')
        nama_ruangan = rooms_map.get(booking.room_id, '-')
        results.append({
            'booking_id': booking.booking_id,
            'nama_event': nama_event,
            'nama_ruangan': nama_ruangan,
            'tanggal_booking': booking.tanggal_booking.strftime('%Y-%m-%d %H:%M:%S'),
            'tanggal_mulai': booking.tanggal_mulai.strftime('%Y-%m-%d'),
            'tanggal_selesai': booking.tanggal_selesai.strftime('%Y-%m-%d'),
            'status': booking.status_booking,
            'keterangan_reject': booking.keterangan_reject or ""
        })
    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5008, debug=True)
