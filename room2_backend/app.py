"""app.py — Room 2: The Data Backend (Flask entry point)."""
import os, sys, traceback
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

PARENT_DIR = os.path.dirname(BASE_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from api.session_routes  import session_bp
from api.classify_routes import classify_bp
from api.risk_routes     import risk_bp
from database.db         import init_db

app = Flask(__name__)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin']  = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PATCH, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/api/session',  methods=['OPTIONS'])
@app.route('/api/sessions', methods=['OPTIONS'])
@app.route('/api/classify', methods=['OPTIONS'])
@app.route('/api/risk',     methods=['OPTIONS'])
def handle_options():
    from flask import Response
    return Response(status=200)

@app.errorhandler(Exception)
def handle_exception(e):
    tb = traceback.format_exc()
    print('=== UNHANDLED ERROR ===')
    print(tb)
    from flask import jsonify
    return jsonify({'error': str(e), 'traceback': tb}), 500

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret')

app.register_blueprint(session_bp,  url_prefix='/api')
app.register_blueprint(classify_bp, url_prefix='/api')
app.register_blueprint(risk_bp,     url_prefix='/api')

with app.app_context():
    init_db()

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    app.run(debug=True, port=port)