from flask import Flask, render_template, request, jsonify
import requests
import os
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
app.secret_key = "frontend-secret-key"
CORS(app)

# URL backend event service (port 5007)
ADD_EVENT_SERVICE = os.getenv("ADD_EVENT_SERVICE_URL", "http://localhost:5007")

@app.route('/')
def index():
    return render_template('event.html', current_year=datetime.now().year)

@app.route('/api/events', methods=['POST'])
def add_event():
    try:
        data = request.json

        required_fields = ['nama_event', 'deskripsi', 'tanggal_mulai', 'tanggal_selesai']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400

        # Forward POST ke backend service
        response = requests.post(f"{ADD_EVENT_SERVICE}/api/events", json=data)
        return jsonify(response.json()), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/events', methods=['GET'])
def get_events():
    try:
        response = requests.get(f"{ADD_EVENT_SERVICE}/api/events")
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5006, debug=True)
