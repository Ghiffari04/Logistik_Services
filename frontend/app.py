from flask import Flask, render_template, request, jsonify
import requests
import os
from ariadne import QueryType, MutationType, make_executable_schema, gql, convert_kwargs_to_snake_case
from ariadne.wsgi import GraphQL
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
app.secret_key = "frontend-secret-key"
CORS(app)  # Enable CORS with default config

# URL provider services (gunakan env var kalau ada)
ROOM_AVAILABILITY_SERVICE = os.getenv("ROOM_AVAILABILITY_SERVICE_URL", "http://localhost:5001")
ROOM_RECOMMENDATION_SERVICE = os.getenv("ROOM_RECOMMENDATION_SERVICE_URL", "http://localhost:5002")
ROOM_BOOKING_SERVICE = os.getenv("ROOM_BOOKING_SERVICE_URL", "http://localhost:5003")
BOOKING_CONFIRMATION_SERVICE = os.getenv("BOOKING_CONFIRMATION_SERVICE_URL", "http://localhost:5004")
ROOM_SCHEDULE_SERVICE = os.getenv("ROOM_SCHEDULE_SERVICE_URL", "http://localhost:5005")

# Routes
@app.route('/')
def index():
    return render_template('index.html', current_year=datetime.now().year)


@app.route('/rooms')
def rooms_page():
    return render_template('rooms.html', current_year=datetime.now().year)

@app.route('/bookings')
def bookings_page():
    return render_template('bookings.html', current_year=datetime.now().year)

@app.route('/schedules')
def schedules_page():
    return render_template('schedules.html', current_year=datetime.now().year)

@app.route('/services')
def services_page():
    return render_template('services.html', current_year=datetime.now().year)

# REST API routes
@app.route('/api/rooms', methods=['GET'])
def get_rooms():
    try:
        response = requests.get(f"{ROOM_AVAILABILITY_SERVICE}/rooms")
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException:
        return jsonify({"error": "Failed to connect to Room Service"}), 503

@app.route('/api/rooms/recommend', methods=['GET'])
def recommend_rooms():
    try:
        params = request.args.to_dict()
        response = requests.get(f"{ROOM_RECOMMENDATION_SERVICE}/recommend-rooms", params=params)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException:
        return jsonify({"error": "Failed to connect to Recommendation Service"}), 503

@app.route('/api/bookings', methods=['POST'])
def create_booking():
    try:
        data = request.json
        response = requests.post(f"{ROOM_BOOKING_SERVICE}/book-room", json=data)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException:
        return jsonify({"error": "Failed to connect to Booking Service"}), 503

@app.route('/api/bookings/<int:event_id>', methods=['GET'])
def get_booking(event_id):
    try:
        response = requests.get(f"{ROOM_BOOKING_SERVICE}/bookings/{event_id}")
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException:
        return jsonify({"error": "Failed to connect to Booking Service"}), 503

@app.route('/api/schedules/<int:room_id>', methods=['GET'])
def get_schedules(room_id):
    try:
        params = request.args.to_dict()
        response = requests.get(f"{ROOM_SCHEDULE_SERVICE}/schedules/{room_id}", params=params)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException:
        return jsonify({"error": "Failed to connect to Schedule Service"}), 503

# GraphQL Schema Definition
type_defs = gql("""
    type Room {
        id: Int!
        name: String!
        capacity: Int!
        facilities: [String!]!
        isAvailable: Boolean!
    }

    type Booking {
        id: Int!
        eventId: Int!
        roomId: Int!
        status: String!
        startTime: String!
        endTime: String!
    }

    type Schedule {
        id: Int!
        roomId: Int!
        eventName: String!
        startTime: String!
        endTime: String!
    }

    input RoomRecommendationInput {
        capacity: Int!
        facilities: [String!]!
        startTime: String!
        endTime: String!
    }

    input BookingInput {
        eventId: Int!
        roomId: Int!
        startTime: String!
        endTime: String!
    }

    type Query {
        rooms: [Room!]!
        recommendedRooms(params: RoomRecommendationInput!): [Room!]!
        booking(eventId: Int!): Booking
        schedules(roomId: Int!, startDate: String, endDate: String): [Schedule!]!
    }

    type Mutation {
        createBooking(bookingData: BookingInput!): Booking!
    }
""")

query = QueryType()
mutation = MutationType()

@query.field("rooms")
def resolve_rooms(_, info):
    try:
        response = requests.get(f"{ROOM_AVAILABILITY_SERVICE}/rooms")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return []

@query.field("recommendedRooms")
@convert_kwargs_to_snake_case
def resolve_recommended_rooms(_, info, params):
    try:
        # Ariadne akan mengirim params sebagai dict
        response = requests.get(f"{ROOM_RECOMMENDATION_SERVICE}/recommend-rooms", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return []

@query.field("booking")
def resolve_booking(_, info, event_id):
    try:
        response = requests.get(f"{ROOM_BOOKING_SERVICE}/bookings/{event_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

@query.field("schedules")
@convert_kwargs_to_snake_case
def resolve_schedules(_, info, room_id, start_date=None, end_date=None):
    try:
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        response = requests.get(f"{ROOM_SCHEDULE_SERVICE}/schedules/{room_id}", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return []

@mutation.field("createBooking")
@convert_kwargs_to_snake_case
def resolve_create_booking(_, info, booking_data):
    try:
        response = requests.post(f"{ROOM_BOOKING_SERVICE}/book-room", json=booking_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

schema = make_executable_schema(type_defs, query, mutation)

# Buat GraphQL app dengan ariadne.wsgi.GraphQL
graphql_app = GraphQL(schema, debug=True)

# Buat route flask untuk GraphQL endpoint yang memanggil graphql_app
@app.route("/graphql", methods=["GET", "POST"])
def graphql_server():
    # Ariadne GraphQL adalah WSGI app, jadi kita panggil dengan environ dan start_response Flask
    from werkzeug.wrappers import Request, Response

    request_ = Request(request.environ)
    response = graphql_app(request_.environ, lambda status, headers: None)
    # response adalah iterable, kita gabungkan jadi satu body string
    response_body = b"".join(response).decode()
    return Response(response_body, mimetype="application/json")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
