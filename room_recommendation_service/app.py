from flask import Flask, request, jsonify
import requests
from datetime import datetime
import os

app = Flask(__name__)

ROOM_AVAILABILITY_SERVICE = "http://room_availability_service:5001"

@app.route('/recommend-rooms', methods=['GET'])
def recommend_rooms():
    # Get parameters
    kapasitas = request.args.get('kapasitas', type=int)
    tanggal_mulai = request.args.get('tanggal_mulai')
    tanggal_selesai = request.args.get('tanggal_selesai')
    fasilitas = request.args.get('fasilitas', '')

    if not all([kapasitas, tanggal_mulai, tanggal_selesai]):
        return jsonify({'error': 'Missing required parameters'}), 400

    try:
        # Get all rooms from availability service
        response = requests.get(f"{ROOM_AVAILABILITY_SERVICE}/rooms")
        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch rooms'}), 500
        
        rooms = response.json()
        
        # Filter rooms based on capacity and facilities
        suitable_rooms = []
        for room in rooms:
            if room['kapasitas'] >= kapasitas:
                if fasilitas:
                    if fasilitas.lower() in room['fasilitas'].lower():
                        # Check availability
                        avail_response = requests.get(
                            f"{ROOM_AVAILABILITY_SERVICE}/check-availability",
                            params={
                                'room_id': room['room_id'],
                                'start_date': tanggal_mulai,
                                'end_date': tanggal_selesai
                            }
                        )
                        
                        if avail_response.status_code == 200:
                            availability = avail_response.json()
                            if availability['is_available']:
                                suitable_rooms.append(room)
                else:
                    # Check availability without facilities requirement
                    avail_response = requests.get(
                        f"{ROOM_AVAILABILITY_SERVICE}/check-availability",
                        params={
                            'room_id': room['room_id'],
                            'start_date': tanggal_mulai,
                            'end_date': tanggal_selesai
                        }
                    )
                    
                    if avail_response.status_code == 200:
                        availability = avail_response.json()
                        if availability['is_available']:
                            suitable_rooms.append(room)

        # Sort rooms by capacity (closest to requested capacity first)
        suitable_rooms.sort(key=lambda x: abs(x['kapasitas'] - kapasitas))
        
        return jsonify({
            'recommended_rooms': suitable_rooms,
            'total_recommendations': len(suitable_rooms)
        })

    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Service communication error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002) 