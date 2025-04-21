from flask import Flask, render_template, request, redirect, url_for, jsonify
from sqlalchemy import func, extract, distinct
from sqlalchemy.orm import joinedload
from collections import defaultdict
from datetime import datetime, timedelta, date
from decimal import Decimal
from flask import request, jsonify
# 替代 dateutil 的相对日期函数，以防导入失败
def custom_relativedelta(dt1, dt2):
    years = dt1.year - dt2.year
    if (dt1.month, dt1.day) < (dt2.month, dt2.day):
        years -= 1
    return type('obj', (object,), {'years': years})

try:
    from dateutil.relativedelta import relativedelta
except ImportError:
    relativedelta = custom_relativedelta

import os
import json
import random
import calendar
import click

# 导入模型和初始化函数
from models import db, Dish, Inventory, Vendor, Purchase, PurchaseItem, Sale
from models import SaleDish, Customer, Staff, Feedback, Payable, Receivable
from db_init import init_db_data, init_db

# Import Blueprints
from blueprints.inventory_bp import inventory_bp, inventory_api
from blueprints.item_bp import item_bp, item_api
from blueprints.order_bp import order_bp, order_api
from blueprints.product_bp import product_bp, product_api
from blueprints.financial_bp import financial_bp, financial_api
from blueprints.dashboard_bp import dashboard_bp, dashboard_api
from blueprints.sales_bp import sales_api
from blueprints.dishes_bp import dishes_bp, dishes_api
from blueprints.staff_bp import staff_bp, staff_api
from blueprints.vendor_bp import vendor_bp, vendor_api
from blueprints.senior_bp import senior_bp
# 初始化 Flask 应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'kaoshan_pizza_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kaoshan_pizza.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Register Blueprints
app.register_blueprint(inventory_bp)
app.register_blueprint(inventory_api)
app.register_blueprint(item_bp, url_prefix='/items')
app.register_blueprint(item_api)
app.register_blueprint(order_bp, url_prefix='/orders')
app.register_blueprint(order_api)
app.register_blueprint(product_bp)
app.register_blueprint(product_api)
app.register_blueprint(financial_bp)
app.register_blueprint(financial_api)
app.register_blueprint(dashboard_bp)
app.register_blueprint(dashboard_api)
app.register_blueprint(dishes_bp, url_prefix='/dishes')
app.register_blueprint(dishes_api)
app.register_blueprint(sales_api)
app.register_blueprint(staff_bp)
app.register_blueprint(staff_api)
app.register_blueprint(vendor_bp)
app.register_blueprint(vendor_api)
app.register_blueprint(senior_bp)
# CLI commands
@app.cli.command('seed-db')
def seed_db_command():
    """Command line: Initialize database data"""
    with app.app_context():
        init_db_data()
    click.echo('Database initialization completed.')

@app.cli.command('init-db')
def init_db_command():
    """Command line: Create database tables and initialize data"""
    with app.app_context():
        init_db()
    click.echo('Database created and initialized successfully.')

# 主路由
@app.route('/')
def index():
    return render_template('welcome.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return redirect(url_for('dashboard_bp.sales_dashboard'))

@app.route('/customer_insights')
def customer_insights():
    return render_template('customer_insights.html')

@app.route('/customers/management')
def customer_management():
    return render_template('customer_management.html')

# —— 新增：创建客户 —— #
@app.route('/api/customers', methods=['POST'])
def create_customer():
    data = request.get_json()
    required = ['Name', 'PhoneNum', 'Email', 'MemLevel', 'BirthDate']
    if not all(field in data for field in required):
        return jsonify({'error': 'Missing field'}), 400

    new_cust = Customer(
        Name=data['Name'],
        PhoneNum=data['PhoneNum'],
        Email=data['Email'],
        MemLevel=data['MemLevel'],
        BirthDate=datetime.fromisoformat(data['BirthDate']),
        RegDate=datetime.utcnow(),
        last_visit=datetime.utcnow()
    )
    db.session.add(new_cust)
    db.session.commit()
    return jsonify(new_cust.to_dict()), 201
# —— 创建客户接口结束 —— #

# 重定向旧链接
@app.route('/customer_management')
def customer_management_redirect():
    return redirect('/customers/management')

@app.route('/products/')
def products_redirect():
    return redirect('/products')

@app.route('/inventory/')
def inventory_redirect():
    return redirect('/inventory')
@app.route('/api/inventory/<int:inventory_id>', methods=['PUT'])
def update_inventory(inventory_id):
    inv = Inventory.query.get_or_404(inventory_id)
    data = request.get_json() or {}

    # 根据前端提交更新字段
    if 'StockLevel' in data:
        inv.StockLevel = data['StockLevel']
    if 'ReorderLevel' in data:
        inv.ReorderLevel = data['ReorderLevel']
    if 'VendorID' in data:
        inv.VendorID = data['VendorID']  # 可为 None
    inv.last_update = datetime.utcnow()  # 更新时间

    db.session.commit()
    return jsonify(inv.to_dict()), 200

# 客户相关 API
@app.route('/api/customers/segments')
def customer_segments():
    stats = db.session.query(
        Customer.MemLevel,
        func.count(Customer.CustomerID).label('count')
    ).group_by(Customer.MemLevel).all()
    return jsonify({
        'segments': [s[0] for s in stats],
        'counts':   [s[1] for s in stats]
    })

@app.route('/api/customers/inactive')
def inactive_customers():
    three_months_ago = datetime.utcnow() - timedelta(days=90)
    cnt = Customer.query.filter(Customer.last_visit < three_months_ago).count()
    return jsonify({'inactive_count': cnt})

@app.route('/api/customers', methods=['GET'])
def get_customers():
    mem_level   = request.args.get('mem_level', 'all')
    search_term = request.args.get('search', '')
    query = Customer.query

    if mem_level != 'all':
        query = query.filter(Customer.MemLevel == mem_level)
    if search_term:
        query = query.filter(
            Customer.Name.ilike(f'%{search_term}%') |
            Customer.PhoneNum.ilike(f'%{search_term}%') |
            Customer.Email.ilike(f'%{search_term}%')
        )

    customers = query.order_by(Customer.Name).all()
    return jsonify([c.to_dict() for c in customers])
# 页面
@app.route('/staff_management')
def staff_management():
    staff_members = Staff.query.order_by(Staff.join_date.desc()).all()
    return render_template('staff_management.html', staff_members=staff_members)

# API: 列表
@app.route('/api/staff', methods=['GET'])
def get_staff():
    staff_members = Staff.query.order_by(Staff.join_date.desc()).all()
    return jsonify([s.to_dict() for s in staff_members])

# API: 新增
@app.route('/api/staff', methods=['POST'])
def add_staff():
    data = request.get_json() or {}
    if not data.get('name') or not data.get('position'):
        return jsonify({'error':'Name and position required'}), 400

    # 生成 staff_code
    last = Staff.query.order_by(Staff.id.desc()).first()
    num  = int(last.staff_code.replace("ST",""))+1 if last else 1
    code = f"ST{num:03d}"

    join_dt = None
    if data.get('join_date'):
        join_dt = datetime.strptime(data['join_date'],"%Y-%m-%d")

    new = Staff(
        staff_code=code,
        name=data['name'],
        position=data['position'],
        department=data.get('department'),
        email=data.get('email'),
        phone=data.get('phone'),
        join_date=join_dt,
        status=data.get('status','Active'),
        address=data.get('address'),
        performance=int(data.get('performance',0))
    )
    db.session.add(new)
    db.session.commit()
    return jsonify(new.to_dict()), 201

# API: 更新
@app.route('/api/staff/<int:staff_id>', methods=['PUT'])
def update_staff(staff_id):
    s = Staff.query.get_or_404(staff_id)
    data = request.get_json() or {}
    if data.get('name'):      s.name        = data['name']
    if data.get('position'):  s.position    = data['position']
    if data.get('department'):s.department  = data['department']
    if data.get('email'):     s.email       = data['email']
    if data.get('phone'):     s.phone       = data['phone']
    if data.get('join_date'):
        s.join_date = datetime.strptime(data['join_date'],"%Y-%m-%d")
    if data.get('status'):    s.status      = data['status']
    if data.get('address'):   s.address     = data['address']
    if 'performance' in data: s.performance = int(data['performance'])
    db.session.commit()
    return jsonify(s.to_dict())

# API: 删除
@app.route('/api/staff/<int:staff_id>', methods=['DELETE'])
def delete_staff(staff_id):
    s = Staff.query.get_or_404(staff_id)
    db.session.delete(s)
    db.session.commit()
    
    return jsonify({'message':'Deleted'})

# API: 绩效图表
@app.route('/api/staff/performance', methods=['GET'])
def staff_performance():
    all_ = Staff.query.all()
    return jsonify({
        'labels': [s.name for s in all_],
        'data'  : [s.performance or 0 for s in all_]
    })

# API: 分布图表
@app.route('/api/staff/distribution', methods=['GET'])
def staff_distribution():
    from sqlalchemy import func
    results = db.session.query(Staff.department, func.count(Staff.id)).group_by(Staff.department).all()
    return jsonify({
        'labels': [dep or 'Unknown' for dep,_ in results],
        'counts': [cnt for _,cnt in results]
    })
# 供应商管理路由
@app.route('/vendors/management')
def vendor_management():
    return render_template('vendor_management.html')

@app.route('/api/vendors', methods=['GET'])
def get_vendors():
    search_term = request.args.get('search', '')
    query = Vendor.query

    if search_term:
        query = query.filter(
            Vendor.Name.ilike(f'%{search_term}%') |
            Vendor.ContactPhone.ilike(f'%{search_term}%') |
            Vendor.ContactName.ilike(f'%{search_term}%')
        )

    vendors = query.order_by(Vendor.Name).all()
    return jsonify([v.to_dict() for v in vendors])

# 采购管理路由
@app.route('/api/purchases', methods=['GET'])
def get_purchases():
    status    = request.args.get('status', 'all')
    vendor_id = request.args.get('vendor_id')
    query = Purchase.query.options(joinedload(Purchase.vendor))

    if status != 'all':
        query = query.filter(Purchase.Status == status)
    if vendor_id:
        query = query.filter(Purchase.VendorID == vendor_id)

    purchases = query.order_by(Purchase.PurchaseDate.desc()).all()
    return jsonify([p.to_dict() for p in purchases])

# 反馈管理路由
@app.route('/feedback/management')
def feedback_management():
    return redirect(url_for('financial_bp.financial_reports'))

@app.route('/api/feedback', methods=['GET'])
def get_feedback():
    status    = request.args.get('status', 'all')
    rating    = request.args.get('rating')
    query     = Feedback.query.options(joinedload(Feedback.customer))

    if status != 'all':
        query = query.filter(Feedback.Status == status)
    if rating:
        query = query.filter(Feedback.Rating == int(rating))

    feedback = query.order_by(Feedback.FeedbackDate.desc()).all()
    return jsonify([f.to_dict() for f in feedback])

@app.route('/api/feedback/summary', methods=['GET'])
def feedback_summary():
    dist = db.session.query(
        Feedback.Rating,
        func.count(Feedback.FeedbackID).label('count')
    ).group_by(Feedback.Rating).all()
    avg = db.session.query(func.avg(Feedback.Rating)).scalar() or 0
    twelve_weeks_ago = datetime.utcnow() - timedelta(weeks=12)
    trend = db.session.query(
        func.strftime('%Y-%W', Feedback.FeedbackDate).label('week'),
        func.avg(Feedback.Rating).label('avg_rating')
    ).filter(Feedback.FeedbackDate >= twelve_weeks_ago)\
     .group_by(func.strftime('%Y-%W', Feedback.FeedbackDate))\
     .order_by(func.strftime('%Y-%W', Feedback.FeedbackDate)).all()

    return jsonify({
        'rating_distribution': {
            'ratings': [r for r, _ in dist],
            'counts':  [c for _, c in dist]
        },
        'average_rating': float(avg),
        'rating_trend': {
            'weeks':   [w for w, _ in trend],
            'ratings': [float(a) for _, a in trend]
        }
    })

# 财务路由重定向
@app.route('/financial_reports')
def financial_reports():
    return redirect(url_for('financial_bp.financial_reports'))

@app.route('/accounts/receivable')
def accounts_receivable():
    return redirect(url_for('financial_bp.financial_reports'))

@app.route('/accounts/payable')
def accounts_payable():
    return redirect(url_for('financial_bp.financial_reports'))

# 辅助过滤器
@app.template_filter('format_currency')
def format_currency(value):
    return f"${value:.2f}"


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if Dish.query.count() == 0:
            init_db_data()
    app.run(debug=True)
    
    
