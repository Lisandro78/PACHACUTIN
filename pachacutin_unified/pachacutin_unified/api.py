from flask import Blueprint, request, jsonify, current_app
import time, os, json
bp = Blueprint('api', __name__)

# Compatibility endpoints preserved:
# /sensors?t=TIMESTAMP   -> returns same JSON your AppInventor expects
# /recommendation?t=...  -> proxies to internal recommender if present
# /capture               -> triggers camera capture
# /cmd?c=A               -> send letter to Arduino (only if control active)
# /mode?m=sensors|monitor|control|idle

@bp.route('/mode', methods=['GET'])
def mode():
    token = request.args.get('token') or request.headers.get('X-API-Token')
    if token != current_app.config.get('AUTH_TOKEN'):
        return jsonify({'ok': False, 'error': 'token inválido'}), 403
    m = (request.args.get('m') or '').lower()
    if not m:
        return jsonify({'ok': False, 'error': "falta parámetro 'm'"}), 400
    mgr = current_app.module_manager
    if m == 'idle':
        mgr.stop_all()
        return jsonify({'ok': True, 'mode': 'idle'})
    # allowed modes
    if m not in ('sensors','monitor','control','soil'):
        return jsonify({'ok': False, 'error': 'modo desconocido'}), 400
    res = mgr.set_mode(m)
    return jsonify(res)

@bp.route('/sensors', methods=['GET'])
def sensors():
    # original AppInventor calls like /sensors?t=timestamp
    token = request.args.get('t')  # keep compatibility, token not required here
    # return last sensor reading from manager
    data = current_app.module_manager.get_sensor_data()
    # ensure fields your app expects exist
    resp = {
        'soil_type': data.get('soil_type','not found'),
        'temperature': data.get('temperature','not found'),
        'soil_moisture': data.get('soil_moisture','not found'),
        'air_humidity': data.get('air_humidity','not found'),
        # meta
        'ts': data.get('ts', time.strftime('%Y%m%d%H%M%S'))
    }
    return jsonify(resp)

@bp.route('/recommendation', methods=['GET','POST'])
def recommendation():
    # keep same interface as before (/recommendation?t=...)
    # try to call existing recommender in pachacutin_ai if available
    try:
        from pachacutin_ai.recommender import get_recommendation
        # prepare payload from query or json
        payload = request.get_json(silent=True) or dict(request.args)
        res = get_recommendation(payload)
        return jsonify({'recommendation': res})
    except Exception as e:
        # fallback: echo inputs (keeps compatibility)
        return jsonify({'recommendation': 'no_recommender_available', 'error': str(e)})

@bp.route('/capture', methods=['POST','GET'])
def capture():
    # triggers camera capture in CamModule (if active)
    mgr = current_app.module_manager
    ok, info = mgr.capture_image()
    if ok:
        return jsonify({'ok': True, 'path': info})
    else:
        return jsonify({'ok': False, 'error': info}), 500

@bp.route('/cmd', methods=['GET','POST'])
def cmd():
    token = request.args.get('token') or request.headers.get('X-API-Token')
    if token != current_app.config.get('AUTH_TOKEN'):
        return jsonify({'ok': False, 'error': 'token inválido'}), 403
    # support GET ?c=A and POST json {"c":"A"}
    c = request.args.get('c') or (request.get_json(silent=True) or {}).get('c')
    if not c:
        return jsonify({'ok': False, 'error': 'no command provided'}), 400
    c = str(c)[0]
    mgr = current_app.module_manager
    if not mgr.is_active('control'):
        return jsonify({'ok': False, 'error': 'control mode not active'}), 409
    mgr.send_to_gateway(c)
    return jsonify({'ok': True, 'sent': c})
