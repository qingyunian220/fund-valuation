#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金实时估值Web应用 - 后端（多用户版）
"""

from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_cors import CORS
from fund_valuation_test import FundValuationFetcher
import json
import os
from datetime import timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.permanent_session_lifetime = timedelta(days=30)  # 30 天登录有效期
CORS(app)

fetcher = FundValuationFetcher()

# 配置文件
CONFIG_FILE = 'config.json'
# 用户数据文件
USERS_FILE = 'users.json'
# 基金数据文件
FUNDS_FILE = 'funds.json'

# 默认配置
DEFAULT_CONFIG = {
    'enable_auth': True,
    'invite_code': 'fund2026',
    'admin_username': 'admin'
}

# 默认用户数据
DEFAULT_USERS = {
    'admin': {
        'password': '123456'
    }
}

def load_config():
    """加载配置"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return DEFAULT_CONFIG.copy()

def save_config(config):
    """保存配置"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def load_users():
    """加载用户数据"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return DEFAULT_USERS.copy()

def save_users(users):
    """保存用户数据"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def load_funds():
    """加载基金数据（按用户存储）"""
    if os.path.exists(FUNDS_FILE):
        with open(FUNDS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_funds(funds_data):
    """保存基金数据"""
    with open(FUNDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(funds_data, f, ensure_ascii=False, indent=2)

def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        config = load_config()
        if config.get('enable_auth'):
            if 'username' not in session:
                return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_username():
    """获取当前登录用户名"""
    return session.get('username')

def is_admin():
    """检查是否是管理员"""
    config = load_config()
    username = get_current_username()
    return username == config.get('admin_username')

@app.route('/')
@login_required
def index():
    """首页"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'POST':
        users = load_users()
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in users and users[username]['password'] == password:
            session.permanent = True  # 启用永久会话
            session['username'] = username
            return redirect(url_for('index'))
        
        return render_template('login.html', error='用户名或密码错误')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """注册页面"""
    config = load_config()
    if request.method == 'POST':
        users = load_users()
        username = request.form.get('username')
        password = request.form.get('password')
        invite_code = request.form.get('invite_code')
        
        # 验证邀请码
        if invite_code != config.get('invite_code'):
            return render_template('register.html', error='邀请码错误')
        
        # 检查用户名是否已存在
        if username in users:
            return render_template('register.html', error='用户名已存在')
        
        # 创建新用户
        users[username] = {
            'password': password
        }
        save_users(users)
        
        # 自动登录
        session.permanent = True  # 启用永久会话
        session['username'] = username
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """退出登录"""
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/api/funds', methods=['GET'])
@login_required
def get_funds():
    """获取当前用户的基金列表"""
    username = get_current_username()
    funds_data = load_funds()
    user_funds = funds_data.get(username, [])
    return jsonify({'funds': user_funds})

@app.route('/api/funds', methods=['POST'])
@login_required
def add_fund():
    """添加基金（当前用户）"""
    username = get_current_username()
    data = request.get_json()
    code = data.get('code')
    name = data.get('name')
    
    if not code:
        return jsonify({'success': False, 'message': '基金代码不能为空'}), 400
    
    funds_data = load_funds()
    user_funds = funds_data.get(username, [])
    
    # 检查是否已存在
    if any(f['code'] == code for f in user_funds):
        return jsonify({'success': False, 'message': '该基金已存在'}), 400
    
    # 尝试获取基金名称
    if not name:
        fund_data = fetcher.fetch_fundgz(code)
        if fund_data:
            name = fund_data.get('name', code)
        else:
            name = code
    
    user_funds.append({'code': code, 'name': name})
    funds_data[username] = user_funds
    save_funds(funds_data)
    
    return jsonify({'success': True, 'funds': user_funds})

@app.route('/api/funds/<code>', methods=['DELETE'])
@login_required
def delete_fund(code):
    """删除基金（当前用户）"""
    username = get_current_username()
    funds_data = load_funds()
    user_funds = funds_data.get(username, [])
    user_funds = [f for f in user_funds if f['code'] != code]
    funds_data[username] = user_funds
    save_funds(funds_data)
    return jsonify({'success': True, 'funds': user_funds})

@app.route('/api/valuation/<code>', methods=['GET'])
@login_required
def get_valuation(code):
    """获取基金估值"""
    data_source = request.args.get('source', '1', type=int)
    data = fetcher.fetch_valuation(code, data_source)
    if data:
        return jsonify({'success': True, 'data': data})
    else:
        return jsonify({'success': False, 'message': '获取估值失败'}), 400

@app.route('/api/valuation/all', methods=['GET'])
@login_required
def get_all_valuations():
    """获取当前用户所有基金的估值"""
    username = get_current_username()
    funds_data = load_funds()
    user_funds = funds_data.get(username, [])
    results = []
    
    for fund in user_funds:
        data = fetcher.fetch_valuation(fund['code'], 1)
        if data:
            results.append(data)
    
    return jsonify({'success': True, 'valuations': results})

@app.route('/config')
@login_required
def config_page():
    """配置页面（仅管理员）"""
    if not is_admin():
        return redirect(url_for('index'))
    return render_template('config.html')

@app.route('/api/config', methods=['GET'])
@login_required
def get_config():
    """获取配置（仅管理员）"""
    if not is_admin():
        return jsonify({'error': '无权限'}), 403
    config = load_config()
    config_to_return = config.copy()
    return jsonify(config_to_return)

@app.route('/api/config', methods=['POST'])
@login_required
def update_config():
    """更新配置（仅管理员）"""
    if not is_admin():
        return jsonify({'error': '无权限'}), 403
    data = request.get_json()
    config = load_config()
    
    if 'enable_auth' in data:
        config['enable_auth'] = data['enable_auth']
    if 'invite_code' in data:
        config['invite_code'] = data['invite_code']
    if 'admin_username' in data:
        config['admin_username'] = data['admin_username']
    
    save_config(config)
    return jsonify({'success': True})

@app.route('/api/search', methods=['GET'])
@login_required
def search_funds():
    """搜索基金"""
    keyword = request.args.get('keyword', '')
    if not keyword:
        return jsonify({'success': False, 'message': '请输入搜索关键词'})
    
    results = fetcher.search_funds(keyword)
    return jsonify({'success': True, 'funds': results})

@app.route('/api/check-admin')
def check_admin():
    """检查是否是管理员"""
    return jsonify({'is_admin': is_admin()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
