from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///room_schedule.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class RoomSchedule(db.Model):
    schedule_id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, nullable=False)
    tanggal_mulai = db.Column(db.DateTime, nullable=False)
    tanggal_selesai = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(255), nullable=False)
    event_id = db.Column(db.Integer, nullable=False)

# Create tables
with app.app_context():
    db.create_all()

@app.route('/add-schedule', methods=['POST'])
def add_schedule():
    data = request.json
    
    required_fields = ['room_id', 'event_id', 'tanggal_mulai', 'tanggal_selesai', 'status']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        # Convert string dates to datetime objects
        tanggal_mulai = datetime.strptime(data['tanggal_mulai'], '%Y-%m-%d %H:%M:%S')
        tanggal_selesai = datetime.strptime(data['tanggal_selesai'], '%Y-%m-%d %H:%M:%S')
        
        # Check for schedule conflicts
        conflicts = RoomSchedule.query.filter(
            RoomSchedule.room_id == data['room_id'],
            RoomSchedule.tanggal_selesai > tanggal_mulai,
            RoomSchedule.tanggal_mulai < tanggal_selesai
        ).all()
        
        if conflicts:
            return jsonify({
                'error': 'Schedule conflict detected',
                'conflicts': [{
                    'schedule_id': conflict.schedule_id,
                    'event_id': conflict.event_id,
                    'tanggal_mulai': conflict.tanggal_mulai.strftime('%Y-%m-%d %H:%M:%S'),
                    'tanggal_selesai': conflict.tanggal_selesai.strftime('%Y-%m-%d %H:%M:%S')
                } for conflict in conflicts]
            }), 409
        
        # Create new schedule
        schedule = RoomSchedule(
            room_id=data['room_id'],
            event_id=data['event_id'],
            tanggal_mulai=tanggal_mulai,
            tanggal_selesai=tanggal_selesai,
            status=data['status']
        )
        
        db.session.add(schedule)
        db.session.commit()
        
        return jsonify({
            'schedule_id': schedule.schedule_id,
            'message': 'Schedule added successfully'
        })

    except ValueError as e:
        return jsonify({'error': f'Invalid date format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to add schedule: {str(e)}'}), 500

@app.route('/schedules/<int:room_id>', methods=['GET'])
def get_room_schedules(room_id):
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = RoomSchedule.query.filter_by(room_id=room_id)
        
        if start_date and end_date:
            start = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
            end = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
            query = query.filter(
                RoomSchedule.tanggal_selesai > start,
                RoomSchedule.tanggal_mulai < end
            )
            
        schedules = query.all()
        return jsonify([{
            'schedule_id': schedule.schedule_id,
            'room_id': schedule.room_id,
            'event_id': schedule.event_id,
            'tanggal_mulai': schedule.tanggal_mulai.strftime('%Y-%m-%d %H:%M:%S'),
            'tanggal_selesai': schedule.tanggal_selesai.strftime('%Y-%m-%d %H:%M:%S'),
            'status': schedule.status
        } for schedule in schedules])

    except ValueError as e:
        return jsonify({'error': f'Invalid date format: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to fetch schedules: {str(e)}'}), 500

@app.route('/update-schedule/<int:schedule_id>', methods=['PUT'])
def update_schedule(schedule_id):
    data = request.json
    schedule = RoomSchedule.query.get(schedule_id)
    
    if not schedule:
        return jsonify({'error': 'Schedule not found'}), 404
        
    try:
        if 'tanggal_mulai' in data:
            schedule.tanggal_mulai = datetime.strptime(data['tanggal_mulai'], '%Y-%m-%d %H:%M:%S')
        if 'tanggal_selesai' in data:
            schedule.tanggal_selesai = datetime.strptime(data['tanggal_selesai'], '%Y-%m-%d %H:%M:%S')
        if 'status' in data:
            schedule.status = data['status']
            
        db.session.commit()
        
        return jsonify({
            'schedule_id': schedule.schedule_id,
            'message': 'Schedule updated successfully'
        })
        
    except ValueError as e:
        return jsonify({'error': f'Invalid date format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update schedule: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005) 