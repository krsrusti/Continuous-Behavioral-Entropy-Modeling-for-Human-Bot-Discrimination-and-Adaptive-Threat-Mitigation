"""app.py — Room 2: The Data Backend (Flask entry point)."""
import os, sys, traceback
from flask import Flask, jsonify, Response
from dotenv import load_dotenv
from database.db import init_db, Session    

load_dotenv()

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from api.session_routes    import session_bp
from api.classify_routes   import classify_bp
from api.risk_routes       import risk_bp
from api.experiment_routes import experiment_bp
from database.db           import init_db
from models                import session_model      # noqa
from models                import experiment_model   # noqa

app = Flask(__name__)

@app.teardown_appcontext
def shutdown_session(exception=None):
    Session.remove()

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin']  = 'http://localhost:8080'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PATCH, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

@app.before_request
def handle_options():
    from flask import request
    if request.method == 'OPTIONS':
        return Response(status=200)

@app.errorhandler(Exception)
def handle_exception(e):
    tb = traceback.format_exc()
    print('=== UNHANDLED ERROR ===')
    print(tb)
    return jsonify({'error': str(e), 'traceback': tb}), 500

@app.errorhandler(404)
def handle_404(e):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(405)
def handle_405(e):
    return jsonify({'error': 'Method not allowed'}), 405

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret')

app.register_blueprint(session_bp,    url_prefix='/api')
app.register_blueprint(classify_bp,   url_prefix='/api')
app.register_blueprint(risk_bp,       url_prefix='/api')
app.register_blueprint(experiment_bp, url_prefix='/api')

@app.route('/api/health', methods=['GET'])
def health():
    try:
        from database.db             import get_db
        from models.session_model    import SessionModel
        from models.experiment_model import ExperimentModel
        db               = get_db()
        session_count    = db.query(SessionModel).count()
        experiment_count = db.query(ExperimentModel).count()
        return jsonify({
            'status':      'ok',
            'sessions':    session_count,
            'experiments': experiment_count,
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'detail': str(e)}), 500

with app.app_context():
    init_db()
    print('[TIF] Database initialised — tables: sessions, experiments')

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    print(f'[TIF] Starting on http://localhost:{port}')
    print(f'[TIF] Health check: http://localhost:{port}/api/health')
    app.run(debug=True, port=port)