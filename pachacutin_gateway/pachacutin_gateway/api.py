from flask import Blueprint, request, jsonify, current_app
bp = Blueprint('api', __name__)

@bp.route('/cmd', methods=['GET','POST'])
def cmd():
    # token simple
    token = request.args.get('token') or request.headers.get('X-API-Token')
    if token != current_app.config.get('AUTH_TOKEN'):
        return jsonify({'ok': False, 'error': 'token inválido'}), 403

    # lee comando: ?c=A o JSON {"c":"A"}
    c = request.args.get('c')
    if not c:
        try:
            payload = request.get_json(silent=True) or {}
            c = payload.get('c')
        except Exception:
            c = None

    if not c:
        return jsonify({'ok': False, 'error': 'no command (c) provided'}), 400

    c = str(c)[0]  # sólo primer carácter
    # la cola la inyecta run.py en app.serial_queue
    q = getattr(current_app, 'serial_queue', None)
    if q is None:
        return jsonify({'ok': False, 'error': 'serial queue not available on server'}), 500
    q.put(c)
    return jsonify({'ok': True, 'sent': c})
