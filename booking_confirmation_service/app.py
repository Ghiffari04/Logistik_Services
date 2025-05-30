from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import requests
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)  # Enable CORS with default config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///booking_confirmation.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

ROOM_BOOKING_SERVICE = "http://room_booking_service:5003"
ROOM_SCHEDULE_SERVICE = "http://room_schedule_service:5005"

class EventApprovalLog(db.Model):from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import requests
from datetime import datetime
import os
import logging

app = Flask(__name__)
CORS(app)  # Enable CORS with default config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///booking_confirmation.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

ROOM_BOOKING_SERVICE = "http://room_booking_service:5003"
ROOM_SCHEDULE_SERVICE = "http://room_schedule_service:5005"

class EventApprovalLog(db.Model):
    approval_id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, nullable=False)
    tanggal_approval = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(255), nullable=False)
    catatan = db.Column(db.String(1000))

# Create tables
with app.app_context():
    db.create_all()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/confirm-booking', methods=['POST'])
def confirm_booking():
    data = request.json
    
    required_fields = ['event_id', 'status', 'catatan']
    if not all(field in data for field in required_fields):
        logger.error('Missing required fields')
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        # Get booking details
        booking_response = requests.get(f"{ROOM_BOOKING_SERVICE}/bookings/{data['event_id']}")
        if booking_response.status_code != 200:
            logger.error('Failed to fetch booking details')
            return jsonify({'error': 'Failed to fetch booking details'}), 500
        
        booking = booking_response.json()
        
        # Create approval log
        approval = EventApprovalLog(
            event_id=data['event_id'],
            tanggal_approval=datetime.now(),
            status=data['status'],
            catatan=data['catatan']
        )
        
        db.session.add(approval)
        db.session.commit()
        
        # If approved, update room schedule
        if data['status'].upper() == 'APPROVED':
            schedule_data = {
                'room_id': booking['room_id'],
                'event_id': data['event_id'],
                'tanggal_mulai': data['tanggal_mulai'],
                'tanggal_selesai': data['tanggal_selesai'],
                'status': 'CONFIRMED'
            }
            
            schedule_response = requests.post(
                f"{ROOM_SCHEDULE_SERVICE}/add-schedule",
                json=schedule_data
            )
            
            if schedule_response.status_code != 200:
                logger.error('Failed to update room schedule')
                return jsonify({'error': 'Failed to update room schedule'}), 500
        
        logger.info('Booking confirmation processed successfully')
        return jsonify({
            'approval_id': approval.approval_id,
            'status': approval.status,
            'message': 'Booking confirmation processed successfully'
        })

    except requests.exceptions.RequestException as e:
        logger.error(f'Service communication error: {str(e)}')
        return jsonify({'error': f'Service communication error: {str(e)}'}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f'Confirmation failed: {str(e)}')
        return jsonify({'error': f'Confirmation failed: {str(e)}'}), 500

@app.route('/approval-status/<int:event_id>', methods=['GET'])
def get_approval_status(event_id):
    approval = EventApprovalLog.query.filter_by(event_id=event_id).first()
    if not approval:
        logger.error('Approval record not found')
        return jsonify({'error': 'Approval record not found'}), 404
        
    logger.info('Approval status retrieved successfully')
    return jsonify({
        'approval_id': approval.approval_id,
        'event_id': approval.event_id,
        'tanggal_approval': approval.tanggal_approval.strftime('%Y-%m-%d %H:%M:%S'),
        'status': approval.status,
        'catatan': approval.catatan
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004)
    approval_id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, nullable=False)
    tanggal_approval = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(255), nullable=False)
    catatan = db.Column(db.String(1000))

# Create tables
with app.app_context():
    db.create_all()

@app.route('/confirm-booking', methods=['POST'])
def confirm_booking():
    data = request.json
    
    required_fields = ['event_id', 'status', 'catatan']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        # Get booking details
        booking_response = requests.get(f"{ROOM_BOOKING_SERVICE}/bookings/{data['event_id']}")
        if booking_response.status_code != 200:
            return jsonify({'error': 'Failed to fetch booking details'}), 500
        
        booking = booking_response.json()
        
        # Create approval log
        approval = EventApprovalLog(
            event_id=data['event_id'],
            tanggal_approval=datetime.now(),
            status=data['status'],
            catatan=data['catatan']
        )
        
        db.session.add(approval)
        db.session.commit()
        
        # If approved, update room schedule
        if data['status'].upper() == 'APPROVED':
            schedule_data = {
                'room_id': booking['room_id'],
                'event_id': data['event_id'],
                'tanggal_mulai': data['tanggal_mulai'],
                'tanggal_selesai': data['tanggal_selesai'],
                'status': 'CONFIRMED'
            }
            
            schedule_response = requests.post(
                f"{ROOM_SCHEDULE_SERVICE}/add-schedule",
                json=schedule_data
            )
            
            if schedule_response.status_code != 200:
                return jsonify({'error': 'Failed to update room schedule'}), 500
        
        return jsonify({
            'approval_id': approval.approval_id,
            'status': approval.status,
            'message': 'Booking confirmation processed successfully'
        })

    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Service communication error: {str(e)}'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Confirmation failed: {str(e)}'}), 500

@app.route('/approval-status/<int:event_id>', methods=['GET'])
def get_approval_status(event_id):
    approval = EventApprovalLog.query.filter_by(event_id=event_id).first()
    if not approval:
        return jsonify({'error': 'Approval record not found'}), 404
        
    return jsonify({
        'approval_id': approval.approval_id,
        'event_id': approval.event_id,
        'tanggal_approval': approval.tanggal_approval.strftime('%Y-%m-%d %H:%M:%S'),
        'status': approval.status,
        'catatan': approval.catatan
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004) 