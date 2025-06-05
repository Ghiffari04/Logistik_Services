from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import requests
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS with default config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///room_booking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

ROOM_AVAILABILITY_SERVICE = "http://room_availability_service:5001"
ADD_EVENT_SERVICE = "http://add_event_service:5007"

class Booking(db.Model):
    booking_id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, nullable=False)
    room_id = db.Column(db.Integer, nullable=False)
    tanggal_booking = db.Column(db.DateTime, nullable=False)
    status_booking = db.Column(db.String(255), nullable=False)

# Create tables
with app.app_context():
    db.create_all()

@app.route('/api/book-room', methods=['POST'])
def book_room():
    data = request.json

    required_fields = ['nama_event', 'deskripsi', 'tanggal_mulai', 'tanggal_selesai', 'room_id']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        # Kirim event ke add_event_service
        event_payload = {
            'nama_event': data['nama_event'],
            'deskripsi': data['deskripsi'],
            'tanggal_mulai': data['tanggal_mulai'],
            'tanggal_selesai': data['tanggal_selesai']
        }

        event_response = requests.post(f"{ADD_EVENT_SERVICE}/api/events", json=event_payload)

        if event_response.status_code not in [200, 201]:
            return jsonify({'error': 'Failed to create event'}), 500

        event_data = event_response.json()
        event_id = event_data.get('event_id')
        if not event_id:
            return jsonify({'error': 'Missing event_id in response'}), 500

        # Cek ketersediaan ruangan
        availability_response = requests.get(
            f"{ROOM_AVAILABILITY_SERVICE}/check-availability",
            params={
                'room_id': data['room_id'],
                'start_date': data['tanggal_mulai'],
                'end_date': data['tanggal_selesai']
            }
        )

        if availability_response.status_code != 200:
            return jsonify({'error': 'Failed to check room availability'}), 500

        availability = availability_response.json()
        if not availability['is_available']:
            return jsonify({
                'error': 'Room is not available for the requested time slot',
                'conflicts': availability.get('conflicting_schedules', [])
            }), 409

        # Simpan booking baru
        booking = Booking(
            event_id=event_id,
            room_id=data['room_id'],
            tanggal_booking=datetime.now(),
            status_booking='PENDING'
        )

        db.session.add(booking)
        db.session.commit()

        return jsonify({
            'booking_id': booking.booking_id,
            'event_id': event_id,
            'status': 'PENDING',
            'message': 'Booking & event created successfully'
        })

    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Service communication error: {str(e)}'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Booking failed: {str(e)}'}), 500

@app.route('/api/bookings/<int:event_id>', methods=['GET'])
def get_booking_status(event_id):
    booking = Booking.query.filter_by(event_id=event_id).first()
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404

    return jsonify({
        'booking_id': booking.booking_id,
        'event_id': booking.event_id,
        'room_id': booking.room_id,
        'tanggal_booking': booking.tanggal_booking.strftime('%Y-%m-%d %H:%M:%S'),
        'status': booking.status_booking
    })

# Tambahan route alias /bookings/<event_id>
@app.route('/bookings/<int:event_id>', methods=['GET'])
def get_booking_status_alias(event_id):
    return get_booking_status(event_id)

@app.route('/api/events')
def proxy_events():
    
    try:
        resp = requests.get("http://add_event_service:5007/api/events")
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)
