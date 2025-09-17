from flask import Blueprint, request, jsonify, current_app
import time

bp = Blueprint('api', __name__)

# =========================
# /mode  (activa módulos)
# =========================
@bp.route('/mode', methods=['GET'])
def mode():
    token = request.args.get('token') or request.headers.get('X-API-Token')
    if token != current_app.config.get('AUTH_TOKEN'):
        return jsonify({'ok': False, 'error': 'forbidden'}), 403

    m = (request.args.get('m') or '').lower().strip()
    if not m:
        return jsonify({'ok': False, 'error': "missing param 'm'"}), 400
    if m not in ('idle', 'sensors', 'monitor', 'control', 'soil'):
        return jsonify({'ok': False, 'error': 'unknown mode'}), 400

    mgr = current_app.module_manager
    if m == 'idle':
        mgr.stop_all()
        return jsonify({'ok': True, 'mode': 'idle'})

    res = mgr.set_mode(m)
    return jsonify(res), (200 if res.get('ok') else 500)

# =========================
# /sensors  (compat App Inventor)
# =========================
@bp.route('/sensors', methods=['GET'])
def sensors():
    # Mantiene compat: App Inventor ya pasa ?t=<timestamp>
    data = current_app.module_manager.get_sensor_data()
    resp = {
        'soil_type':     data.get('soil_type', 'not found'),
        'temperature':   data.get('temperature', 'not found'),
        'soil_moisture': data.get('soil_moisture', 'not found'),
        'air_humidity':  data.get('air_humidity', 'not found'),
        'ts':            data.get('ts', time.strftime('%Y%m%d%H%M%S')),
    }
    return jsonify(resp)

# =========================
# /recommendation  (opcional)
# =========================
@bp.route('/recommendation', methods=['GET', 'POST'])
def recommendation():
    payload = request.get_json(silent=True) or dict(request.args)
    try:
        # Si tienes un módulo propio de recomendación, impórtalo aquí:
        # from pachacutin_ai.recommender import get_recommendation
        # res = get_recommendation(payload)
        # return jsonify({'recommendation': res})
        return jsonify({'recommendation': 'no_recommender_available', 'echo': payload})
    except Exception as e:
        return jsonify({'recommendation': 'error', 'error': str(e)}), 500

# =========================
# /capture (GET y POST)
# =========================
@bp.route('/capture', methods=['GET', 'POST'])
def capture():
    mgr = current_app.module_manager
    ok, info = mgr.capture_image()
    if ok:
        return jsonify({'ok': True, 'path': info})
    return jsonify({'ok': False, 'error': info}), 500

# =========================
# /cmd  (puente App→Python→Arduino)
# =========================
@bp.route('/cmd', methods=['GET', 'POST'])
def cmd():
    token = request.args.get('token') or request.headers.get('X-API-Token')
    if token != current_app.config.get('AUTH_TOKEN'):
        return jsonify({'ok': False, 'error': 'forbidden'}), 403

    c = request.args.get('c') or ((request.get_json(silent=True) or {}).get('c'))
    if not c:
        return jsonify({'ok': False, 'error': 'missing param c'}), 400
    c = str(c)[0]  # solo 1 char

    mgr = current_app.module_manager
    if not mgr.is_active('control'):
        return jsonify({'ok': False, 'error': 'control mode not active'}), 409

    try:
        mgr.send_to_gateway(c)
        return jsonify({'ok': True, 'sent': c})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500
