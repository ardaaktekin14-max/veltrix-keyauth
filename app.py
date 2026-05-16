from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import json
import os
import uuid
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'veltrix-super-secret-2024')

ADMINS = {
    os.environ.get('ADMIN1_USER', 'Arda'): os.environ.get('ADMIN1_PASS', 'Vx#9mK$2pL@qZ7!rN'),
    os.environ.get('ADMIN2_USER', 'Furkan'): os.environ.get('ADMIN2_PASS', 'Jw&8nT#5bY@kM3$xQ'),
}

KEYS_FILE = 'keys.json'

def load_keys():
    if not os.path.exists(KEYS_FILE):
        return {}
    with open(KEYS_FILE, 'r') as f:
        return json.load(f)

def save_keys(keys):
    with open(KEYS_FILE, 'w') as f:
        json.dump(keys, f, indent=2)

def generate_key():
    return 'VLTX-' + str(uuid.uuid4()).upper().replace('-', '')[:20]

@app.route('/')
def index():
    if not session.get('admin'):
        return redirect(url_for('login'))
    keys = load_keys()
    now = datetime.utcnow()
    for k, v in keys.items():
        if v['expires'] != 'lifetime':
            exp = datetime.fromisoformat(v['expires'])
            v['expired'] = exp < now
            v['expires_display'] = exp.strftime('%d/%m/%Y %H:%M')
        else:
            v['expired'] = False
            v['expires_display'] = 'Ömür Boyu'
    return render_template('panel.html', keys=keys, admin_name=session.get('admin_name'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if username in ADMINS and ADMINS[username] == password:
            session['admin'] = True
            session['admin_name'] = username
            return redirect(url_for('index'))
        error = 'Kullanıcı adı veya şifre yanlış!'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/create_key', methods=['POST'])
def create_key():
    if not session.get('admin'):
        return redirect(url_for('login'))
    duration = request.form.get('duration')
    note = request.form.get('note', '')
    custom_key = request.form.get('custom_key', '').strip()
    
    if custom_key:
        key = custom_key
    else:
        key = generate_key()
    
    keys = load_keys()
    
    if key in keys:
        return redirect(url_for('index'))
    
    if duration == 'lifetime':
        expires = 'lifetime'
    else:
        days = int(duration)
        expires = (datetime.utcnow() + timedelta(days=days)).isoformat()
    keys[key] = {
        'created': datetime.utcnow().isoformat(),
        'expires': expires,
        'note': note,
        'hwid': None,
        'active': True,
        'created_by': session.get('admin_name')
    }
    save_keys(keys)
    return redirect(url_for('index'))
    if not session.get('admin'):
        return redirect(url_for('login'))
    duration = request.form.get('duration')
    note = request.form.get('note', '')
    key = generate_key()
    keys = load_keys()
    if duration == 'lifetime':
        expires = 'lifetime'
    else:
        days = int(duration)
        expires = (datetime.utcnow() + timedelta(days=days)).isoformat()
    keys[key] = {
        'created': datetime.utcnow().isoformat(),
        'expires': expires,
        'note': note,
        'hwid': None,
        'active': True,
        'created_by': session.get('admin_name')
    }
    save_keys(keys)
    return redirect(url_for('index'))

@app.route('/delete_key/<key>')
def delete_key(key):
    if not session.get('admin'):
        return redirect(url_for('login'))
    keys = load_keys()
    if key in keys:
        del keys[key]
        save_keys(keys)
    return redirect(url_for('index'))

@app.route('/reset_hwid/<key>')
def reset_hwid(key):
    if not session.get('admin'):
        return redirect(url_for('login'))
    keys = load_keys()
    if key in keys:
        keys[key]['hwid'] = None
        save_keys(keys)
    return redirect(url_for('index'))

@app.route('/api/verify', methods=['POST'])
def verify():
    data = request.get_json()
    if not data:
        return jsonify({'valid': False, 'message': 'Geçersiz istek'})
    key = data.get('key', '').strip()
    hwid = data.get('hwid', '').strip()
    if not key or not hwid:
        return jsonify({'valid': False, 'message': 'Key veya HWID eksik'})
    keys = load_keys()
    if key not in keys:
        return jsonify({'valid': False, 'message': 'Geçersiz key!'})
    k = keys[key]
    if not k.get('active', True):
        return jsonify({'valid': False, 'message': 'Key deaktif edilmiş!'})
    if k['expires'] != 'lifetime':
        exp = datetime.fromisoformat(k['expires'])
        if datetime.utcnow() > exp:
            return jsonify({'valid': False, 'message': 'Key süresi dolmuş!'})
    if k['hwid'] is None:
        keys[key]['hwid'] = hwid
        save_keys(keys)
    elif k['hwid'] != hwid:
        return jsonify({'valid': False, 'message': 'Bu key başka bir bilgisayara kayıtlı!'})
    return jsonify({'valid': True, 'message': 'Hoş geldin!'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
