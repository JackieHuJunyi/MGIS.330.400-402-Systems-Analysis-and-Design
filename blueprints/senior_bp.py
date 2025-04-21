from flask import Blueprint, render_template
from datetime import datetime, date
from sqlalchemy import func
from models import db, Sale, Customer

senior_bp = Blueprint('senior_bp', __name__,
                      template_folder='../templates',
                      url_prefix='/finance')
@senior_bp.route('/senior-discounts')
def senior_discounts_report():
    try:
        today = date.today()
        age_threshold = 60
        # 计算 60 岁及以上的出生日期上限，比如今天是 2025-04-20，则 cutoff_date = 1965-04-20
        cutoff_date = date(today.year - age_threshold, today.month, today.day)

        # 只统计 60 岁及以上客户的已完成订单折扣总额和次数
        result = db.session.query(
            func.sum(Sale.DiscountAmount).label('total_discount'),
            func.count(Sale.SaleID).label('discount_count')
        ).join(Customer, Sale.CustomerID == Customer.CustomerID)\
         .filter(
             Sale.Status == 'Completed',
             Customer.BirthDate <= cutoff_date
         ).one()

        total_discount = result.total_discount or 0
        discount_count  = result.discount_count  or 0

        # 列出所有符合年龄条件的客户详情
        seniors = db.session.query(Customer)\
            .filter(Customer.BirthDate <= cutoff_date)\
            .order_by(Customer.BirthDate)\
            .all()

        qualified = [
            {
                'name' : c.Name,
                'birth': c.BirthDate.strftime('%Y-%m-%d'),
                'age'  : today.year - c.BirthDate.year 
                          - ((today.month, today.day) < (c.BirthDate.month, c.BirthDate.day))
            }
            for c in seniors
        ]

        return render_template('senior_discounts.html',
                               total_discount=total_discount,
                               discount_count=discount_count,
                               senior_customers=qualified,
                               today=today)

    except Exception as e:
        return f"Error generating report: {e}", 500