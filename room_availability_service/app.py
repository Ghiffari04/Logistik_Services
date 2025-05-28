from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///room_availability.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class Room(db.Model):
    room_id = db.Column(db.Integer, primary_key=True)
    nama_ruangan = db.Column(db.String(255), nullable=False)
    kapasitas = db.Column(db.Integer, nullable=False)
    fasilitas = db.Column(db.String(1000))
    lokasi = db.Column(db.String(255))

class RoomSchedule(db.Model):
    schedule_id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.room_id'), nullable=False)
    tanggal_mulai = db.Column(db.DateTime, nullable=False)
    tanggal_selesai = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(255))
    event_id = db.Column(db.Integer)

# Create tables
with app.app_context():
    db.create_all()

@app.route('/rooms', methods=['GET'])
def get_rooms():
    rooms = Room.query.all()
    return jsonify([{
        'room_id': room.room_id,
        'nama_ruangan': room.nama_ruangan,
        'kapasitas': room.kapasitas,
        'fasilitas': room.fasilitas,
        'lokasi': room.lokasi
    } for room in rooms])

@app.route('/check-availability', methods=['GET'])
def check_availability():
    room_id = request.args.get('room_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not all([room_id, start_date, end_date]):
        return jsonify({'error': 'Missing parameters'}), 400
    
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
        end_date = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    # Check for conflicting schedules
    conflicts = RoomSchedule.query.filter(
        RoomSchedule.room_id == room_id,
        RoomSchedule.tanggal_selesai > start_date,
        RoomSchedule.tanggal_mulai < end_date
    ).all()

    is_available = len(conflicts) == 0
    
    return jsonify({
        'room_id': room_id,
        'is_available': is_available,
        'conflicting_schedules': [{
            'schedule_id': conflict.schedule_id,
            'tanggal_mulai': conflict.tanggal_mulai.strftime('%Y-%m-%d %H:%M:%S'),
            'tanggal_selesai': conflict.tanggal_selesai.strftime('%Y-%m-%d %H:%M:%S')
        } for conflict in conflicts]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001) 