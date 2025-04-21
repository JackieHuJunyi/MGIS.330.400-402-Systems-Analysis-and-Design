from flask import Blueprint, render_template, jsonify, redirect, url_for
from sqlalchemy import func, extract, distinct
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta, date
from decimal import Decimal

from models import db, Sale, SaleDish, Customer, Staff, Dish, Payable, Receivable

# 创建蓝图
dashboard_bp = Blueprint('dashboard_bp', __name__, 
                         template_folder='../templates',
                         url_prefix='/dashboard')

# 创建API蓝图
dashboard_api = Blueprint('dashboard_api', __name__, 
                          url_prefix='/api/dashboard')

# 仪表盘路由
@dashboard_bp.route('/sales')
def sales_dashboard():
    """销售仪表盘页面"""
    # 获取今日日期
    today = date.today()
    
    # 获取最新订单数据（最多5条）作为预加载数据传递给模板
    recent_sales = Sale.query.options(joinedload(Sale.customer), 
                                    joinedload(Sale.items).joinedload(SaleDish.dish))\
                            .filter(func.date(Sale.SaleDate) <= today)\
                            .order_by(Sale.SaleDate.desc())\
                            .limit(5)\
                            .all()
    
    # 将订单数据转换为字典并确保items属性是一个列表
    recent_sales_data = []
    for sale in recent_sales:
        sale_dict = sale.to_dict()
        # 确保items是列表而不是函数或其他不可索引对象
        if hasattr(sale, 'items'):
            sale_dict['items'] = [item.to_dict() for item in sale.items]
        else:
            sale_dict['items'] = []
        recent_sales_data.append(sale_dict)
    
    # 获取今日销售额和订单数量
    today_sales = db.session.query(func.sum(Sale.TotalAmount))\
        .filter(Sale.Status == 'Completed')\
        .filter(func.date(Sale.SaleDate) == today)\
        .scalar() or 0
    
    # 计算今日订单数
    today_orders = db.session.query(func.count(Sale.SaleID))\
        .filter(func.date(Sale.SaleDate) == today)\
        .scalar() or 0
    
    # 计算月度销售额
    month_start = date(today.year, today.month, 1)
    monthly_sales = db.session.query(func.sum(Sale.TotalAmount))\
        .filter(Sale.Status == 'Completed')\
        .filter(func.date(Sale.SaleDate) >= month_start)\
        .filter(func.date(Sale.SaleDate) <= today)\
        .scalar() or 0
    
    # 计算平均订单金额
    avg_order = db.session.query(func.avg(Sale.TotalAmount))\
        .filter(Sale.Status == 'Completed')\
        .filter(func.date(Sale.SaleDate) <= today)\
        .scalar() or 0
    
    # 将额外的数据传递给模板
    dashboard_data = {
        'today_sales': float(today_sales),
        'today_orders': int(today_orders),
        'monthly_sales': float(monthly_sales),
        'avg_order': float(avg_order),
        'recent_sales': recent_sales_data
    }
    
    return render_template('sales_dashboard.html', dashboard_data=dashboard_data)

# 仪表盘API路由
@dashboard_api.route('/sales_summary')
def dashboard_sales_summary():
    """销售汇总数据API"""
    # 获取今日日期
    today = date.today()
    yesterday = today - timedelta(days=1)
    month_start = date(today.year, today.month, 1)
    prev_month_end = month_start - timedelta(days=1)
    prev_month_start = date(prev_month_end.year, prev_month_end.month, 1)
    
    # 计算今日销售额
    today_sales = db.session.query(func.sum(Sale.TotalAmount))\
        .filter(Sale.Status == 'Completed')\
        .filter(func.date(Sale.SaleDate) == today)\
        .scalar() or 0
    
    # 计算昨日销售额（用于计算增长率）
    yesterday_sales = db.session.query(func.sum(Sale.TotalAmount))\
        .filter(Sale.Status == 'Completed')\
        .filter(func.date(Sale.SaleDate) == yesterday)\
        .scalar() or 0
    
    # 计算本月销售额
    monthly_sales = db.session.query(func.sum(Sale.TotalAmount))\
        .filter(Sale.Status == 'Completed')\
        .filter(func.date(Sale.SaleDate) >= month_start)\
        .filter(func.date(Sale.SaleDate) <= today)\
        .scalar() or 0
    
    # 计算上月销售额（用于计算增长率）
    prev_month_sales = db.session.query(func.sum(Sale.TotalAmount))\
        .filter(Sale.Status == 'Completed')\
        .filter(func.date(Sale.SaleDate) >= prev_month_start)\
        .filter(func.date(Sale.SaleDate) <= prev_month_end)\
        .scalar() or 0
    
    # 计算今日订单数
    today_orders = db.session.query(func.count(Sale.SaleID))\
        .filter(func.date(Sale.SaleDate) == today)\
        .scalar() or 0
    
    # 计算昨日订单数（用于计算增长率）
    yesterday_orders = db.session.query(func.count(Sale.SaleID))\
        .filter(func.date(Sale.SaleDate) == yesterday)\
        .scalar() or 0
    
    # 计算平均订单金额
    avg_order = db.session.query(func.avg(Sale.TotalAmount))\
        .filter(Sale.Status == 'Completed')\
        .filter(func.date(Sale.SaleDate) <= today)\
        .scalar() or 0
    
    # 计算上月平均订单金额（用于计算增长率）
    prev_avg_order = db.session.query(func.avg(Sale.TotalAmount))\
        .filter(Sale.Status == 'Completed')\
        .filter(func.date(Sale.SaleDate) >= prev_month_start)\
        .filter(func.date(Sale.SaleDate) <= prev_month_end)\
        .scalar() or 0
    
    # 计算增长率
    today_growth = ((today_sales - yesterday_sales) / yesterday_sales * 100) if yesterday_sales > 0 else 0
    monthly_growth = ((monthly_sales - prev_month_sales) / prev_month_sales * 100) if prev_month_sales > 0 else 0
    orders_growth = ((today_orders - yesterday_orders) / yesterday_orders * 100) if yesterday_orders > 0 else 0
    avg_growth = ((avg_order - prev_avg_order) / prev_avg_order * 100) if prev_avg_order > 0 else 0
    
    return jsonify({
        'today_sales': float(today_sales),
        'monthly_sales': float(monthly_sales),
        'orders_count': int(today_orders),
        'avg_order_amount': float(avg_order),
        'today_growth': float(today_growth),
        'monthly_growth': float(monthly_growth),
        'orders_growth': float(orders_growth),
        'avg_growth': float(avg_growth)
    })

@dashboard_api.route('/top_products')
def dashboard_top_products():
    """热门产品数据API"""
    # 查询最畅销的菜品（按销售数量）
    top_dishes_by_quantity = db.session.query(
        Dish.DishID,
        Dish.Name,
        Dish.Price,
        func.sum(SaleDish.Quantity).label('total_sold')
    ).join(SaleDish, Dish.DishID == SaleDish.DishID)\
     .join(Sale, SaleDish.SaleID == Sale.SaleID)\
     .filter(Sale.Status == 'Completed')\
     .group_by(Dish.DishID, Dish.Name, Dish.Price)\
     .order_by(func.sum(SaleDish.Quantity).desc())\
     .limit(10)\
     .all()
    
    # 查询最畅销的菜品（按销售额）
    top_dishes_by_revenue = db.session.query(
        Dish.DishID,
        Dish.Name,
        Dish.Price,
        func.sum(SaleDish.Quantity * Dish.Price).label('total_revenue')
    ).join(SaleDish, Dish.DishID == SaleDish.DishID)\
     .join(Sale, SaleDish.SaleID == Sale.SaleID)\
     .filter(Sale.Status == 'Completed')\
     .group_by(Dish.DishID, Dish.Name, Dish.Price)\
     .order_by(func.sum(SaleDish.Quantity * Dish.Price).desc())\
     .limit(10)\
     .all()
    
    return jsonify({
        'by_quantity': [
            {
                'id': item.DishID,
                'name': item.Name,
                'price': float(item.Price),
                'quantity': int(item.total_sold)
            } for item in top_dishes_by_quantity
        ],
        'by_revenue': [
            {
                'id': item.DishID,
                'name': item.Name,
                'price': float(item.Price),
                'revenue': float(item.total_revenue)
            } for item in top_dishes_by_revenue
        ]
    })

@dashboard_api.route('/sales_distribution')
def dashboard_sales_distribution():
    """销售分布数据API"""
    # 获取过去30天的数据范围
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    # 按类别分布
    sales_by_category = db.session.query(
        Dish.Category,
        func.sum(SaleDish.Quantity * Dish.Price).label('total_sales')
    ).join(SaleDish, Dish.DishID == SaleDish.DishID)\
     .join(Sale, SaleDish.SaleID == Sale.SaleID)\
     .filter(Sale.Status == 'Completed')\
     .filter(Sale.SaleDate >= thirty_days_ago)\
     .group_by(Dish.Category)\
     .all()

    # 按时段分布（早餐、午餐、晚餐、夜宵）
    # 定义时段范围
    time_periods = {
        'breakfast': (6, 10),  # 早上6点到10点
        'lunch': (11, 14),     # 上午11点到下午2点
        'dinner': (17, 20),    # 下午5点到晚上8点
        'late_night': (21, 23) # 晚上9点到11点
    }
    
    sales_by_period = {}
    for period, (start_hour, end_hour) in time_periods.items():
        total = db.session.query(func.sum(Sale.TotalAmount))\
            .filter(Sale.Status == 'Completed')\
            .filter(Sale.SaleDate >= thirty_days_ago)\
            .filter(extract('hour', Sale.SaleDate) >= start_hour)\
            .filter(extract('hour', Sale.SaleDate) <= end_hour)\
            .scalar() or 0
        sales_by_period[period] = float(total)
    
    # 按客户类型分布（会员等级）
    sales_by_membership = db.session.query(
        Customer.MemLevel,
        func.sum(Sale.TotalAmount).label('total_sales')
    ).join(Sale, Customer.CustomerID == Sale.CustomerID)\
     .filter(Sale.Status == 'Completed')\
     .filter(Sale.SaleDate >= thirty_days_ago)\
     .group_by(Customer.MemLevel)\
     .all()

    return jsonify({
        'by_category': {
            'categories': [item[0] if item[0] else 'Unknown' for item in sales_by_category],
            'sales': [float(item[1]) for item in sales_by_category]
        },
        'by_period': {
            'periods': list(sales_by_period.keys()),
            'sales': list(sales_by_period.values())
        },
        'by_membership': {
            'levels': [item[0] if item[0] else 'Non-member' for item in sales_by_membership],
            'sales': [float(item[1]) for item in sales_by_membership]
        }
    }) 