from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import graphene
from graphene import ObjectType, String, Int, Field, Mutation

app = Flask(__name__)
CORS(app)
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
            'schedule_id': c.schedule_id,
            'tanggal_mulai': c.tanggal_mulai.strftime('%Y-%m-%d %H:%M:%S'),
            'tanggal_selesai': c.tanggal_selesai.strftime('%Y-%m-%d %H:%M:%S')
        } for c in conflicts]
    })

# GraphQL schema

class RoomType(graphene.ObjectType):
    room_id = Int()
    nama_ruangan = String()
    kapasitas = Int()
    fasilitas = String()
    lokasi = String()

class CreateRoom(Mutation):
    class Arguments:
        nama_ruangan = String(required=True)
        kapasitas = Int(required=True)
        fasilitas = String()
        lokasi = String()

    room = Field(lambda: RoomType)

    def mutate(self, info, nama_ruangan, kapasitas, fasilitas=None, lokasi=None):
        room = Room(
            nama_ruangan=nama_ruangan,
            kapasitas=kapasitas,
            fasilitas=fasilitas,
            lokasi=lokasi
        )
        db.session.add(room)
        db.session.commit()
        return CreateRoom(room=room)

class Query(ObjectType):
    hello = String(default_value="GraphQL Ready!")
    rooms = graphene.List(RoomType)

    def resolve_rooms(root, info):
        return Room.query.all()

class Mutation(ObjectType):
    create_room = CreateRoom.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)

@app.route("/graphql", methods=["GET", "POST"])
def graphql():
    if request.method == "GET":
        # Optional: serve simple GraphiQL UI for testing
        graphiql_html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>GraphiQL</title>
            <link href="https://cdn.jsdelivr.net/npm/graphiql@2.0.9/graphiql.min.css" rel="stylesheet" />
        </head>
        <body style="margin: 0;">
            <div id="graphiql" style="height: 100vh;"></div>
            <script crossorigin src="https://cdn.jsdelivr.net/npm/react@18/umd/react.production.min.js"></script>
            <script crossorigin src="https://cdn.jsdelivr.net/npm/react-dom@18/umd/react-dom.production.min.js"></script>
            <script crossorigin src="https://cdn.jsdelivr.net/npm/graphiql@2.0.9/graphiql.min.js"></script>
            <script>
                const graphQLFetcher = graphQLParams =>
                    fetch('/graphql', {
                        method: 'post',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(graphQLParams),
                    })
                    .then(response => response.json())
                    .catch(error => {
                        console.error('Fetch error:', error);
                        return { errors: [{ message: error.message }] };
                    });

                const rootElement = document.getElementById('graphiql');
                if (ReactDOM.createRoot) {
                    ReactDOM.createRoot(rootElement).render(
                        React.createElement(GraphiQL, { fetcher: graphQLFetcher })
                    );
                } else {
                    ReactDOM.render(
                        React.createElement(GraphiQL, { fetcher: graphQLFetcher }),
                        rootElement
                    );
                }
            </script>
        </body>
        </html>
        '''
        return graphiql_html, 200, {'Content-Type': 'text/html'}

    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400

    result = schema.execute(
        data.get("query"),
        variables=data.get("variables"),
        operation_name=data.get("operationName"),
        context_value=request,
    )

    response = {}
    if result.errors:
        response["errors"] = [str(e) for e in result.errors]
    if result.data:
        response["data"] = result.data

    status_code = 200 if not result.errors else 400
    return jsonify(response), status_code

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
