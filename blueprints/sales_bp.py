from flask import Blueprint, jsonify, request
from sqlalchemy import func, extract
from datetime import datetime, timedelta, date
from models import db, Sale, SaleDish, Dish, Customer, Staff

# 创建销售API蓝图
sales_api = Blueprint('sales_api', __name__, url_prefix='/api/sales')

@sales_api.route('/top_dishes')
def top_dishes():
    """获取最畅销菜品数据"""
    # 查询最畅销的菜品
    top_selling = db.session.query(
        Dish.Name,
        func.sum(SaleDish.Quantity).label('total_sold')
    ).join(SaleDish, Dish.DishID == SaleDish.DishID)\
     .join(Sale, SaleDish.SaleID == Sale.SaleID)\
     .filter(Sale.Status == 'Completed')\
     .group_by(Dish.Name)\
     .order_by(func.sum(SaleDish.Quantity).desc())\
     .limit(5)\
     .all()

    return jsonify({
        'labels': [item[0] for item in top_selling],
        'data': [int(item[1]) for item in top_selling]
    })

@sales_api.route('/trend')
def sales_trend():
    """获取销售趋势数据"""
    # 获取当前日期
    today = date.today()
    
    # 创建最近30天的日期列表
    date_range = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(29, -1, -1)]
    
    # 查询销售趋势（按天）
    sales_by_day = db.session.query(
        func.date(Sale.SaleDate).label('date'),
        func.sum(Sale.TotalAmount).label('total_sales')
    ).filter(Sale.Status == 'Completed')\
     .filter(func.date(Sale.SaleDate) <= today)\
     .group_by(func.date(Sale.SaleDate))\
     .order_by(func.date(Sale.SaleDate).desc())\
     .limit(30)\
     .all()

    # 将查询结果转换为字典，方便按日期查找
    sales_dict = {}
    for item in sales_by_day:
        if isinstance(item.date, str):
            date_str = item.date
        else:
            date_str = item.date.strftime('%Y-%m-%d')
        sales_dict[date_str] = float(item.total_sales)
    
    # 确保所有最近30天的日期都有数据，没有的用0填充
    dates = date_range
    sales = [sales_dict.get(date_str, 0) for date_str in date_range]

    return jsonify({
        'dates': dates,
        'sales': sales
    })

@sales_api.route('/by_channel')
def sales_by_channel():
    """获取按渠道划分的销售数据"""
    # 查询按渠道划分的销售数据
    channel_sales = db.session.query(
        Sale.Channel,
        func.sum(Sale.TotalAmount).label('total_sales')
    ).filter(Sale.Status == 'Completed')\
     .group_by(Sale.Channel)\
     .all()

    return jsonify({
        'channels': [item[0] if item[0] else 'Unknown' for item in channel_sales],
        'sales': [float(item[1]) for item in channel_sales]
    })

@sales_api.route('/peak_hours')
def sales_peak_hours():
    """获取销售高峰时段数据"""
    # 查询高峰时段数据
    peak_hours = db.session.query(
        extract('hour', Sale.SaleDate).label('hour'),
        func.count(Sale.SaleID).label('order_count')
    ).filter(Sale.Status.in_(['Completed', 'Delivered']))\
    .group_by(extract('hour', Sale.SaleDate))\
    .order_by(extract('hour', Sale.SaleDate))\
         .all()

    hours = [item[0] for item in peak_hours]
    counts = [item[1] for item in peak_hours]
    
    # 格式化小时标签
    hour_labels = [f"{int(hour)}:00" for hour in hours]

    return jsonify({
        'hours': hour_labels,
        'counts': counts
    })

@sales_api.route('/<int:sale_id>', methods=['GET'])
def get_sale_detail(sale_id):
    """获取单个销售订单的详细信息"""
    try:
        sale = db.session.query(Sale).get(sale_id)
        if not sale:
            return jsonify({"error": "Sale not found"}), 404

        customer = db.session.query(Customer).get(sale.CustomerID)

        # 查询SaleDish和Dish来获取菜品信息
        items = db.session.query(
                SaleDish.Quantity,
                SaleDish.UnitPrice,
                Dish.Name.label('DishName'),
                Dish.DishID
            ).join(Dish, SaleDish.DishID == Dish.DishID)\
             .filter(SaleDish.SaleID == sale_id).all()

        sale_details = {
            'SaleID': sale.SaleID,
            'SaleDate': sale.SaleDate.strftime('%Y-%m-%d %H:%M:%S') if sale.SaleDate else None,
            'CustomerName': customer.Name if customer else 'Guest',
            'CustomerID': sale.CustomerID,
            'TotalAmount': float(sale.TotalAmount) if sale.TotalAmount else 0.0,
            'DiscountAmount': float(sale.DiscountAmount) if sale.DiscountAmount else 0.0,
            'FinalAmount': float(sale.TotalAmount - (sale.DiscountAmount or 0)) if sale.TotalAmount else 0.0,
            'Status': sale.Status,
            'Channel': sale.Channel,
            'OrderType': sale.OrderType,
            'items': [
                {
                    'DishID': item.DishID,
                    'DishName': item.DishName,
                    'Quantity': item.Quantity,
                    'UnitPrice': float(item.UnitPrice) if item.UnitPrice else 0.0,
                    'Subtotal': float(item.UnitPrice * item.Quantity) if item.UnitPrice else 0.0
                } for item in items
            ]
        }
        return jsonify(sale_details)

    except Exception as e:
        return jsonify({"error": "Could not fetch sale details", "details": str(e)}), 500

@sales_api.route('/<int:sale_id>/status', methods=['PUT'])
def update_sale_status(sale_id):
    """更新销售订单状态"""
    data = request.get_json()
    new_status = data.get('status')

    if not new_status:
        return jsonify({'error': 'New status is required.'}), 400

    allowed_statuses = ['Pending', 'Processing', 'Delivered', 'Completed', 'Cancelled']
    if new_status not in allowed_statuses:
         return jsonify({'error': f'Invalid status value. Allowed statuses: {", ".join(allowed_statuses)}'}), 400

    try:
        sale = Sale.query.get_or_404(sale_id)
        sale.Status = new_status
        db.session.commit()

        return jsonify({'success': True, 'message': f'Sale #{sale_id} status updated to {new_status}.', 'new_status': new_status})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'An error occurred while updating the sale status.'}), 500 