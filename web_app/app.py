import sys
import os
import hashlib
import math
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, session
from functools import wraps
from dateutil.relativedelta import relativedelta

# Add the parent directory to path so we can import existing modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DBManager
from controllers.finance_controller import FinanceController

# ── App Setup ──────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder='static', static_url_path='')
# SECRET_KEY: leer desde variable de entorno para que las sesiones
# sobrevivan reinicios del contenedor
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(32))
sync_token_env = os.environ.get('SYNC_TOKEN')
if not sync_token_env:
    import uuid
    sync_token_env = uuid.uuid4().hex
    print(f"\n⚠️  SYNC_TOKEN no configurado. Usando token temporal: {sync_token_env}")
    print("   Configure SYNC_TOKEN en producción para usar un token fijo.\n")
os.environ['SYNC_TOKEN'] = sync_token_env

# Database path: en Docker usa el volumen /data; en local usa ~/Shark Contabilidad
data_dir = os.environ.get('DATA_DIR', os.path.join(os.path.expanduser('~'), 'Shark Contabilidad'))
os.makedirs(data_dir, exist_ok=True)
db_path = os.path.join(data_dir, 'budget_app.db')

db_manager = DBManager(db_path)
controller = FinanceController(db_manager)

# ── Auth Helpers ────────────────────────────────────────────────────────────────
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('authenticated'):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

# ── Static / PWA ───────────────────────────────────────────────────────────────
@app.route('/')
def index():
    response = send_from_directory('static', 'index.html')
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response

@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')

@app.route('/sw.js')
def service_worker():
    response = send_from_directory('static', 'sw.js')
    response.headers['Content-Type'] = 'application/javascript; charset=utf-8'
    return response

@app.route('/css/app.css')
def css():
    response = send_from_directory('static/css', 'app.css')
    response.headers['Content-Type'] = 'text/css; charset=utf-8'
    return response

@app.route('/js/app.js')
def js():
    response = send_from_directory('static/js', 'app.js')
    response.headers['Content-Type'] = 'application/javascript; charset=utf-8'
    return response
    response.headers['Service-Worker-Allowed'] = '/'
    response.headers['Cache-Control'] = 'no-cache'
    return response

# ── Auth Routes ─────────────────────────────────────────────────────────────────
@app.route('/api/auth/status')
def auth_status():
    stored_hash = db_manager.get_config('app_password')
    fails = db_manager.get_failed_attempts()
    return jsonify({
        'needs_setup': stored_hash is None,
        'authenticated': session.get('authenticated', False),
        'recovery_mode': fails >= 3 and stored_hash is not None,
        'security_question': db_manager.get_config('security_question') or ''
    })

@app.route('/api/auth/setup', methods=['POST'])
def auth_setup():
    data = request.get_json()
    password = data.get('password', '')
    sq = data.get('sec_question', '').strip()
    sa = data.get('sec_answer', '').strip()
    
    if len(password) < 4:
        return jsonify({'error': 'La contraseña debe tener al menos 4 caracteres'}), 400
    if not sq or not sa:
        return jsonify({'error': 'La pregunta y respuesta de seguridad son obligatorias para el protocolo de autodestrucción'}), 400
        
    hashed = hash_password(password)
    db_manager.set_config('app_password', hashed)
    
    # Save auth recovery
    db_manager.setup_security_question(sq, sa, password)
    
    db_manager.crypto.initialize_from_password(password)
    session['authenticated'] = True
    return jsonify({'success': True})

@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    data = request.get_json()
    password = data.get('password', '')
    
    stored_hash = db_manager.get_config('app_password')
    if stored_hash is None:
        return jsonify({'error': 'No hay contraseña configurada'}), 400
        
    if db_manager.get_failed_attempts() >= 3:
        return jsonify({'error': 'Cuenta bloqueada, requiere recuperación', 'recovery_mode': True}), 403
        
    if hash_password(password) == stored_hash:
        db_manager.crypto.initialize_from_password(password)
        db_manager.reset_failed_attempts()
        session['authenticated'] = True
        return jsonify({'success': True})
        
    wiped = db_manager.increment_failed_attempts()
    fails = db_manager.get_failed_attempts()
    if wiped:
        return jsonify({'error': 'SEGURIDAD CRÍTICA: Demasiados intentos fallidos. La base de datos ha sido purgada y la app se ha reiniciado por defecto.', 'wiped': True}), 401
    elif fails >= 3:
        return jsonify({'error': 'Se han agotado los intentos. Entrando en modo recuperación.', 'recovery_mode': True}), 403
        
    return jsonify({'error': f'Contraseña incorrecta (Fallo {fails}/3)'}), 401

@app.route('/api/auth/recover', methods=['POST'])
def auth_recover():
    data = request.get_json()
    answer = data.get('answer', '')
    
    success, raw_pwd, wiped = db_manager.recover_master_password(answer)
    if wiped:
        return jsonify({'error': 'SEGURIDAD CRÍTICA: La base de datos fue purgada tras agotar todos los intentos.', 'wiped': True}), 401
    
    if success:
        db_manager.crypto.initialize_from_password(raw_pwd)
        session['authenticated'] = True
        return jsonify({'success': True, 'raw_pwd': raw_pwd})
    else:
        fails = db_manager.get_failed_attempts()
        return jsonify({'error': f'Respuesta incorrecta. (Fallo {fails}/5 antes de purga total)'}), 401

@app.route('/api/auth/logout', methods=['POST'])
def auth_logout():
    session.pop('authenticated', None)
    return jsonify({'success': True})

@app.route('/api/auth/password', methods=['PUT'])
@require_auth
def auth_change_password():
    data = request.get_json()
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    
    if len(new_password) < 4:
        return jsonify({'error': 'La nueva contraseña debe tener al menos 4 caracteres'}), 400
        
    success, message = db_manager.change_password(old_password, new_password)
    
    if success:
        # Re-initialize controller with new crypto state isn't strictly necessary 
        # since it uses db_manager's crypto instance, which is updated inside change_password.
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'error': message}), 400


# ── Dashboard ───────────────────────────────────────────────────────────────────
@app.route('/api/dashboard')
@require_auth
def dashboard():
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)
    summary = controller.get_dashboard_summary(year, month)
    trend = controller.get_trend_data(year, month, 6)
    return jsonify({'summary': summary, 'trend': trend})

# ── Categories ──────────────────────────────────────────────────────────────────
@app.route('/api/categories')
@require_auth
def get_categories():
    c_type = request.args.get('type')
    cats = controller.get_categories(c_type)
    return jsonify([{'id': c.id, 'name': c.name, 'type': c.type, 'color': c.color} for c in cats])

@app.route('/api/categories', methods=['POST'])
@require_auth
def add_category():
    data = request.get_json()
    name = data.get('name', '').strip()
    c_type = data.get('type', '')
    color = data.get('color', '#3498DB')
    if not name or c_type not in ('income', 'expense'):
        return jsonify({'error': 'Datos inválidos'}), 400
    cat_id = controller.add_category(name, c_type, color)
    return jsonify({'id': cat_id, 'name': name, 'type': c_type, 'color': color})

@app.route('/api/categories/<int:cat_id>', methods=['DELETE'])
@require_auth
def delete_category(cat_id):
    controller.delete_category(cat_id)
    return jsonify({'success': True})

# ── Transactions ────────────────────────────────────────────────────────────────
@app.route('/api/transactions')
@require_auth
def get_transactions():
    t_type = request.args.get('type')
    txs = controller.get_transactions(t_type)
    cats = {c.id: c for c in controller.get_categories()}
    result = []
    for tx in txs:
        cat = cats.get(tx.category_id)
        result.append({
            'id': tx.id,
            'type': tx.type,
            'name': tx.name,
            'amount': tx.amount,
            'date': tx.date,
            'category_id': tx.category_id,
            'category_name': cat.name if cat else '—',
            'category_color': cat.color if cat else '#888',
            'recurrence_type': tx.recurrence_type,
            'recurrence_interval': tx.recurrence_interval,
            'recurrence_duration': tx.recurrence_duration,
        })
    return jsonify(result)

@app.route('/api/transactions', methods=['POST'])
@require_auth
def add_transaction():
    data = request.get_json()
    try:
        t_type = data['type']
        category_id = int(data['category_id'])
        name = data['name'].strip()
        amount = float(data['amount'])
        date = data['date']
        r_type = data.get('recurrence_type', 'one_time')
        r_interval = int(data.get('recurrence_interval', 1))
        r_duration = data.get('recurrence_duration')
        if r_duration is not None:
            r_duration = int(r_duration)
        if not name or amount <= 0:
            raise ValueError
    except (KeyError, ValueError, TypeError):
        return jsonify({'error': 'Datos inválidos'}), 400

    tx_id = controller.add_transaction(t_type, category_id, name, amount, date, r_type, r_interval, r_duration)
    return jsonify({'id': tx_id, 'success': True})

@app.route('/api/transactions/<int:t_id>', methods=['PUT'])
@require_auth
def update_transaction(t_id):
    data = request.get_json()
    try:
        category_id = int(data['category_id'])
        name = data['name'].strip()
        amount = float(data['amount'])
        date = data['date']
        r_type = data.get('recurrence_type', 'one_time')
        r_interval = int(data.get('recurrence_interval', 1))
        r_duration = data.get('recurrence_duration')
        if r_duration is not None:
            r_duration = int(r_duration)
        if not name or amount <= 0:
            raise ValueError
    except (KeyError, ValueError, TypeError):
        return jsonify({'error': 'Datos inválidos'}), 400

    controller.update_transaction(t_id, category_id, name, amount, date, r_type, r_interval, r_duration)
    return jsonify({'success': True})

@app.route('/api/transactions/<int:t_id>', methods=['DELETE'])
@require_auth
def delete_transaction(t_id):
    controller.delete_transaction(t_id)
    return jsonify({'success': True})

# ── Commitments ─────────────────────────────────────────────────────────────────
@app.route('/api/commitments')
@require_auth
def get_commitments():
    data = controller.get_commitments_with_progress()
    result = []
    for d in data:
        c = d['commitment']
        remaining = d['remaining']
        # Estimate end date
        end_date_str = None
        if remaining > 0 and d['payments']:
            sorted_pays = sorted(d['payments'], key=lambda p: p[3])
            amounts = [p[2] for p in sorted_pays]
            if len(sorted_pays) == 1:
                avg_monthly = amounts[0]
                ref_date = datetime.strptime(sorted_pays[0][3], "%Y-%m-%d")
            else:
                last_date = datetime.strptime(sorted_pays[-1][3], "%Y-%m-%d")
                first_date = datetime.strptime(sorted_pays[0][3], "%Y-%m-%d")
                months_span = max(1, (last_date.year - first_date.year) * 12 + (last_date.month - first_date.month))
                avg_monthly = sum(amounts) / months_span
                ref_date = last_date
            if avg_monthly > 0:
                months_to_go = math.ceil(remaining / avg_monthly)
                end_dt = ref_date + relativedelta(months=months_to_go)
                end_date_str = end_dt.strftime("%d/%m/%Y")

        result.append({
            'id': c.id,
            'name': c.name,
            'total_amount': c.total_amount,
            'date': c.date,
            'total_paid': d['total_paid'],
            'remaining': remaining,
            'progress_pct': d['progress_pct'],
            'end_date': end_date_str,
        })
    return jsonify(result)

@app.route('/api/commitments/summary')
@require_auth
def commitments_summary():
    summary = controller.get_commitments_summary()
    return jsonify(summary)

@app.route('/api/commitments', methods=['POST'])
@require_auth
def add_commitment():
    data = request.get_json()
    name = data.get('name', '').strip()
    try:
        amount = float(data.get('total_amount', 0))
        if not name or amount <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({'error': 'Datos inválidos'}), 400
    date = datetime.now().strftime("%Y-%m-%d")
    c_id = controller.add_commitment(name, amount, date)
    return jsonify({'id': c_id, 'success': True})

@app.route('/api/commitments/<int:c_id>', methods=['DELETE'])
@require_auth
def delete_commitment(c_id):
    controller.delete_commitment(c_id)
    return jsonify({'success': True})

@app.route('/api/commitments/<int:c_id>/payment', methods=['POST'])
@require_auth
def add_commitment_payment(c_id):
    """Add a one-time payment (aportación) to a commitment."""
    data = request.get_json()
    try:
        amount = float(data['amount'])
        date = data['date']
        name = data.get('name', '').strip()
        category_id = int(data['category_id'])
        if amount <= 0 or not name:
            raise ValueError
    except (KeyError, ValueError, TypeError):
        return jsonify({'error': 'Datos inválidos'}), 400

    controller.add_transaction('expense', category_id, name, amount, date, 'one_time', 1, None)
    controller.add_commitment_payment(c_id, amount, date)
    return jsonify({'success': True})

@app.route('/api/commitments/<int:c_id>/plan', methods=['POST'])
@require_auth
def add_commitment_plan(c_id):
    """Add a recurring payment plan to a commitment."""
    data = request.get_json()
    try:
        amount = float(data['amount'])
        date = data['date']
        name = data.get('name', '').strip()
        category_id = int(data['category_id'])
        interval = int(data.get('interval', 1))
        duration = int(data['duration'])
        if amount <= 0 or not name or duration < 1:
            raise ValueError
    except (KeyError, ValueError, TypeError):
        return jsonify({'error': 'Datos inválidos'}), 400

    controller.add_transaction('expense', category_id, name, amount, date, 'custom', interval, duration)
    controller.add_commitment_payment(c_id, amount, date)
    return jsonify({'success': True})

# ── Historic ────────────────────────────────────────────────────────────────────
@app.route('/api/historic')
@require_auth
def historic():
    data = controller.get_full_history_data()
    return jsonify(data)

# ── Financial Health ────────────────────────────────────────────────────────────
@app.route('/api/health')
@require_auth
def financial_health():
    metrics = controller.get_financial_health_metrics()
    return jsonify(metrics)

# ── Savings / Huchas ────────────────────────────────────────────────────────────
@app.route('/api/savings')
@require_auth
def get_savings():
    goals = controller.get_savings_goals_with_progress()
    result = []
    for g in goals:
        goal = g['goal']
        result.append({
            'id': goal.id,
            'name': goal.name,
            'target_amount': goal.target_amount,
            'date': goal.date,
            'total_saved': g['total_saved'],
            'progress_pct': g['progress_pct'],
            'contributions_count': len(g['contributions'])
        })
    return jsonify(result)

@app.route('/api/savings', methods=['POST'])
@require_auth
def add_savings_goal():
    data = request.get_json()
    name = data.get('name', '').strip()
    try:
        amount = float(data.get('target_amount', 0))
        if not name or amount < 0: # 0 is allowed for "No ceiling"
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({'error': 'Datos inválidos'}), 400
    date = datetime.now().strftime("%Y-%m-%d")
    s_id = controller.add_savings_goal(name, amount, date)
    return jsonify({'id': s_id, 'success': True})

@app.route('/api/savings/<int:s_id>', methods=['DELETE'])
@require_auth
def delete_savings_goal(s_id):
    controller.delete_savings_goal(s_id)
    return jsonify({'success': True})

@app.route('/api/savings/<int:s_id>/contribution', methods=['POST'])
@require_auth
def add_savings_contribution(s_id):
    data = request.get_json()
    try:
        amount = float(data['amount'])
        date = data['date']
        name = data.get('name', '').strip()
        category_id = int(data['category_id'])
        if amount <= 0 or not name:
            raise ValueError
    except (KeyError, ValueError, TypeError):
        return jsonify({'error': 'Datos inválidos'}), 400

    controller.add_transaction('expense', category_id, name, amount, date, 'one_time', 1, None)
    controller.add_savings_contribution(s_id, amount, date)
    return jsonify({'success': True})

@app.route('/api/manual')
@require_auth
def get_manual():
    from utils.translator import Translator, tr
    lang = db_manager.get_config('language') or 'es'
    Translator.set_language(lang)
    sections = []
    for i in range(1, 14):
        sections.append({
            'title': tr(f"MANUAL_Q{i}_T"),
            'desc': tr(f"MANUAL_Q{i}_A")
        })
    return jsonify(sections)

# ── Sync Routes ──────────────────────────────────────────────────────────────────
def require_sync_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get('token') or request.headers.get('Authorization')
        if token and token.startswith('Bearer '):
            token = token[7:]
        server_token = os.environ.get('SYNC_TOKEN') or os.environ.get('SYNC_TOKEN', 'no_token_configured')
        if not server_token or server_token == 'no_token_configured' or token != server_token:
            return jsonify({'error': 'Invalid Sync Token'}), 403
        return f(*args, **kwargs)
    return decorated

@app.route('/api/sync/status')
@require_sync_token
def sync_status():
    last_updated = db_manager.get_config('last_updated')
    return jsonify({'last_updated': int(last_updated) if last_updated else 0})

@app.route('/api/sync/download')
@require_sync_token
def sync_download():
    if not os.path.exists(db_path):
        return jsonify({'error': 'DB file not found'}), 404
    return send_from_directory(os.path.dirname(db_path), os.path.basename(db_path), as_attachment=True)

@app.route('/api/sync/upload', methods=['POST'])
@require_sync_token
def sync_upload():
    try:
        temp_path = db_path + '.tmp'
        with open(temp_path, 'wb') as f:
            f.write(request.get_data())
        os.replace(temp_path, db_path)
        
        # Opcional: Reiniciar la conexión local del servidor
        db_manager.get_connection().close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── Run ─────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    # Get local IP for mobile access
    import socket
    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except Exception:
        local_ip = '127.0.0.1'
    
    print("=" * 55)
    print("  🦈 SHARK CONTABILIDAD — Servidor Web")
    print("=" * 55)
    print(f"  💻 Local:    http://localhost:5000")
    print(f"  📱 Móvil:    http://{local_ip}:5000")
    print("  (Abre la URL en el navegador de tu móvil)")
    print("=" * 55)
    
    app.run(host='0.0.0.0', port=5000, debug=False)
