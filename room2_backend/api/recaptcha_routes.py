from flask import Blueprint, request, jsonify
import requests
import os

recaptcha_bp = Blueprint('recaptcha', __name__)

@recaptcha_bp.route('/recaptcha/verify', methods=['POST'])
def verify_recaptcha():

    data = request.get_json(silent=True) or {}

    token = data.get('token')

    if not token:
        return jsonify({
            'success': False,
            'error': 'Missing token'
        }), 400

    secret = os.getenv('RECAPTCHA_SECRET_KEY')

    if not secret:
        return jsonify({
            'success': False,
            'error': 'Secret key not configured'
        }), 500

    try:
        response = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data={
                'secret': secret,
                'response': token
            },
            timeout=10
        )

        result = response.json()

        return jsonify({
            'success': result.get('success', False),
            'score': result.get('score', 0),
            'action': result.get('action'),
            'hostname': result.get('hostname'),
            'raw': result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500