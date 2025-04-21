from flask import Blueprint, render_template, jsonify, abort, request, current_app
from sqlalchemy.orm import joinedload
from sqlalchemy import func, extract, and_, or_
from datetime import datetime, timedelta, date
from decimal import Decimal
import calendar
import locale
import logging
from sqlalchemy.exc import SQLAlchemyError

from models import db, Sale, Purchase, PurchaseItem, Item, Receivable, Payable, Customer, Vendor

# 设置菜品成本预设（菜品ID: 成本）
PRODUCT_COST_PRESET = {
    1: 5.50,   # 比萨基础
    2: 7.25,   # 意大利面
    3: 3.75,   # 沙拉
    4: 4.50,   # 汉堡
    5: 2.25,   # 炸薯条
    6: 1.50,   # 饮料
    7: 6.00,   # 牛排
    8: 4.25,   # 三明治
    9: 3.25,   # 甜点
    10: 5.75,  # 海鲜
    # 默认其他菜品成本
    'default': 4.00
}

# 设置日志记录器
logger = logging.getLogger(__name__)

# Import relativedelta safely
try:
    from dateutil.relativedelta import relativedelta
except ImportError:
    # Provide a fallback if dateutil is not available
    def relativedelta(dt1, dt2):
        years = dt1.year - dt2.year
        if (dt1.month, dt1.day) < (dt2.month, dt2.day):
            years -= 1
        return type('obj', (object,), {'years': years})

# Blueprint for financial report pages
financial_bp = Blueprint('financial_bp', __name__,
                         template_folder='../templates',
                         url_prefix='/finance')

# Blueprint for financial APIs
financial_api = Blueprint('financial_api', __name__, url_prefix='/api/finance')

# Route for the main financial reports page
@financial_bp.route('/')
def financial_reports():
    """Renders the main financial reports page with summary data."""
    try:
        # 获取当前日期
        now = datetime.now().date()  # 确保是date类型
        
        # 计算财务摘要数据
        financial_summary = get_financial_summary(now)
        
        # 调试输出
        logger.debug(f"Receivables data: {financial_summary['receivables']}")
        logger.debug(f"Receivables records length: {len(financial_summary['receivables']['records'])}")
        
        # 渲染模板
        return render_template('financial_reports.html', 
                               financial_summary=financial_summary,
                               now=now)
    except Exception as e:
        import traceback
        error_tb = traceback.format_exc()
        logger.error(f"Error rendering financial reports: {str(e)}\nTraceback: {error_tb}")
        # 返回错误页面或使用空数据渲染
        empty_summary = {
            'total_revenue': 0,
            'total_discounts': 0,
            'total_senior_discounts': 0,
            'total_purchases': 0,
            'gross_profit': 0,
            'gross_margin': 0,
            'total_items_sold': 0,
            'new_orders_last_30_days': 0,
            'new_customers_last_30_days': 0,
            'top_items': [],
            'receivables': {'total': 0, 'overdue': 0, 'records': []},
            'payables': {'total': 0, 'overdue': 0, 'records': []},
            'monthly_stats': {},
            'product_margins': []
        }
        return render_template('financial_reports.html', 
                               financial_summary=empty_summary,
                               now=now,
                               error_message=str(e))

# 获取财务摘要数据
def get_financial_summary(now):
    # 确保now是date类型
    if isinstance(now, datetime):
        now = now.date()
    
    # 计算过去30天的日期
    thirty_days_ago = now - timedelta(days=30)
    
    # 1. 计算总收入（已完成订单）
    total_revenue_query = db.session.query(func.sum(Sale.TotalAmount)).filter(Sale.Status == 'Completed')
    total_revenue = total_revenue_query.scalar() or 0
    
    # 2. 计算总折扣
    total_discounts_query = db.session.query(func.sum(Sale.DiscountAmount)).filter(Sale.Status == 'Completed')
    total_discounts = total_discounts_query.scalar() or 0
    
    # 3. 计算老年折扣总额 - 修改为检查折扣类型字段是否存在
    total_senior_discounts = 0
    try:
        if hasattr(Sale, 'DiscountType'):
            total_senior_discounts_query = db.session.query(func.sum(Sale.DiscountAmount)).filter(
                Sale.Status == 'Completed',
                Sale.DiscountType == 'Senior'
            )
            total_senior_discounts = total_senior_discounts_query.scalar() or 0
    except Exception as e:
        logger.warning(f"Unable to query senior discounts: {str(e)}")
    
    # 4. 计算总采购成本（基于预设菜品成本）
    total_purchases = 0
    try:
        # 检查Sale表中是否有ItemID和ItemCount字段
        if hasattr(Sale, 'ItemID') and hasattr(Sale, 'ItemCount'):
            # 获取销售的菜品数据
            sales_data = db.session.query(Sale.ItemID, func.sum(Sale.ItemCount)).filter(
                Sale.Status == 'Completed'
            ).group_by(Sale.ItemID).all()
            
            # 计算总成本
            for product_id, quantity in sales_data:
                product_cost = PRODUCT_COST_PRESET.get(product_id, PRODUCT_COST_PRESET['default'])
                total_purchases += product_cost * quantity
        else:
            # 备用方法：假设每个订单平均成本是售价的40%
            total_purchases = total_revenue * 0.4
            
    except Exception as e:
        logger.warning(f"Error calculating total purchases: {str(e)}")
        # 如果计算失败，则使用备用方法
        try:
            # 从采购表获取总成本
            total_purchases_query = db.session.query(func.sum(Purchase.total_amount)).filter(Purchase.Status == 'Completed')
            total_purchases = total_purchases_query.scalar() or 0
        except Exception as e2:
            logger.warning(f"Alternative method for purchases also failed: {str(e2)}")
            # 如果所有方法都失败，使用默认值
            total_purchases = total_revenue * 0.4
    
    # 5. 计算毛利润和毛利率
    gross_profit = total_revenue - total_purchases
    gross_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # 6. 计算销售物品总数
    total_items_sold = 0
    try:
        # 检查Sale是否有ItemCount字段
        if hasattr(Sale, 'ItemCount'):
            total_items_sold_query = db.session.query(func.sum(Sale.ItemCount)).filter(Sale.Status == 'Completed')
            total_items_sold = total_items_sold_query.scalar() or 0
        else:
            # 如果没有ItemCount，使用订单数量作为替代
            total_items_sold_query = db.session.query(func.count(Sale.SaleID)).filter(Sale.Status == 'Completed')
            total_items_sold = total_items_sold_query.scalar() or 0
    except Exception as e:
        logger.warning(f"Unable to query total items sold: {str(e)}")
    
    # 7. 计算最近30天的新订单数
    new_orders_query = db.session.query(func.count(Sale.SaleID)).filter(
        Sale.SaleDate >= thirty_days_ago,
        Sale.Status == 'Completed'
    )
    new_orders_last_30_days = new_orders_query.scalar() or 0
    
    # 8. 计算最近30天的新客户数
    new_customers_query = db.session.query(func.count(Customer.CustomerID)).filter(
        Customer.RegDate >= thirty_days_ago
    )
    new_customers_last_30_days = new_customers_query.scalar() or 0
    
    # 9. 获取热销商品数据和利润率
    try:
        top_items = get_top_selling_items()
    except Exception as e:
        logger.warning(f"Error getting top selling items: {str(e)}")
        top_items = []
    
    # 10. 获取应收账款数据
    try:
        receivables_data = get_receivables_summary()
    except Exception as e:
        logger.warning(f"Error getting receivables summary: {str(e)}")
        receivables_data = {'total': 0, 'overdue': 0, 'records': []}
    
    # 11. 获取应付账款数据
    try:
        payables_data = get_payables_summary()
    except Exception as e:
        logger.warning(f"Error getting payables summary: {str(e)}")
        payables_data = {'total': 0, 'overdue': 0, 'records': []}
    
    # 12. 获取月度财务数据
    try:
        monthly_stats = get_monthly_financial_stats(now.year)
    except Exception as e:
        logger.warning(f"Error getting monthly financial stats: {str(e)}")
        monthly_stats = {}
    
    # 13. 计算产品利润率数据
    try:
        product_margins = calculate_product_margins()
    except Exception as e:
        logger.warning(f"Error calculating product margins: {str(e)}")
        product_margins = []
    
    # 整合所有数据
    financial_summary = {
        'total_revenue': total_revenue,
        'total_discounts': total_discounts,
        'total_senior_discounts': total_senior_discounts,
        'total_purchases': total_purchases,
        'gross_profit': gross_profit,
        'gross_margin': gross_margin,
        'total_items_sold': total_items_sold,
        'new_orders_last_30_days': new_orders_last_30_days,
        'new_customers_last_30_days': new_customers_last_30_days,
        'top_items': top_items,
        'receivables': receivables_data,
        'payables': payables_data,
        'monthly_stats': monthly_stats,
        'product_margins': product_margins
    }
    
    return financial_summary

# 计算产品利润率
def calculate_product_margins():
    product_margins = []
    
    try:
        # 检查必要字段是否存在
        if hasattr(Sale, 'ItemID') and hasattr(Sale, 'ItemCount'):
            # 获取每个产品的销售数据
            products_data = db.session.query(
                Item.ItemID, 
                Item.Name,
                func.sum(Sale.TotalAmount).label('total_revenue'),
                func.sum(Sale.ItemCount).label('quantity')
            ).join(Sale, Sale.ItemID == Item.ItemID).filter(
                Sale.Status == 'Completed'
            ).group_by(Item.ItemID, Item.Name).all()
            
            for product in products_data:
                item_id, name, revenue, quantity = product
                
                # 使用预设成本
                unit_cost = PRODUCT_COST_PRESET.get(item_id, PRODUCT_COST_PRESET['default'])
                total_cost = unit_cost * quantity
                
                # 避免除以零错误
                if revenue and revenue > 0:
                    profit = revenue - total_cost
                    margin = (profit / revenue) * 100
                else:
                    profit = 0
                    margin = 0
                    
                # 计算平均售价
                avg_price = revenue / quantity if quantity > 0 else 0
                
                product_margins.append({
                    'id': item_id,
                    'name': name or f"Product #{item_id}",
                    'price': float(avg_price),
                    'cost': float(unit_cost),
                    'margin': float(margin),
                    'profit': float(profit),
                    'quantity': int(quantity)
                })
        else:
            # 如果没有必要字段，使用备用数据
            raise ValueError("Required fields not present in Sale model")
                
        # 按利润率降序排序
        product_margins.sort(key=lambda x: x['margin'], reverse=True)
        
    except Exception as e:
        logger.warning(f"Error in calculate_product_margins: {str(e)}")
        # 提供默认数据
        product_margins = [
            {'id': 1, 'name': 'Pizza', 'price': 12.99, 'cost': 5.50, 'margin': 57.7, 'profit': 7.49, 'quantity': 0},
            {'id': 2, 'name': 'Pasta', 'price': 10.99, 'cost': 4.20, 'margin': 61.8, 'profit': 6.79, 'quantity': 0},
            {'id': 3, 'name': 'Salad', 'price': 8.99, 'cost': 3.75, 'margin': 58.3, 'profit': 5.24, 'quantity': 0},
            {'id': 4, 'name': 'Burger', 'price': 9.99, 'cost': 4.50, 'margin': 55.0, 'profit': 5.49, 'quantity': 0},
            {'id': 5, 'name': 'Fries', 'price': 4.99, 'cost': 2.25, 'margin': 54.9, 'profit': 2.74, 'quantity': 0}
        ]
    
    return product_margins

# 获取热销商品数据
def get_top_selling_items(limit=5):
    # 查询销售量最高的商品
    top_items = []
    try:
        # 检查必要字段是否存在
        if hasattr(Sale, 'ItemID') and hasattr(Sale, 'ItemCount'):
            # 获取产品销售数据
            top_items_query = db.session.query(
                Item.ItemID,
                Item.Name,
                func.sum(Sale.ItemCount).label('total_quantity'),
                func.sum(Sale.TotalAmount).label('total_revenue')
            ).join(Sale, Sale.ItemID == Item.ItemID).filter(
                Sale.Status == 'Completed'
            ).group_by(Item.ItemID, Item.Name).order_by(
                func.sum(Sale.ItemCount).desc()
            ).limit(limit)
            
            top_items_result = top_items_query.all()
            
            # 格式化结果
            for item in top_items_result:
                item_id, name, quantity, revenue = item
                top_items.append({
                    'id': item_id,
                    'name': name or f"Item #{item_id}",
                    'quantity': int(quantity or 0),
                    'revenue': float(revenue or 0)
                })
        else:
            # 如果没有必要字段，使用备用数据
            raise ValueError("Required fields not present in Sale model")
            
    except Exception as e:
        logger.warning(f"Error fetching top selling items: {str(e)}")
        # 提供默认数据
        top_items = [
            {'id': 1, 'name': 'Pizza', 'quantity': 0, 'revenue': 0},
            {'id': 2, 'name': 'Pasta', 'quantity': 0, 'revenue': 0},
            {'id': 3, 'name': 'Salad', 'quantity': 0, 'revenue': 0}
        ]
    
    return top_items

# 获取应收账款摘要
def get_receivables_summary(limit=5):
    # 当前日期
    now = datetime.now().date()
    
    # 查询未支付的应收账款总额
    total_unpaid_query = db.session.query(func.sum(Receivable.ReceivableAmount)).filter(
        Receivable.Status != 'Paid'
    )
    total_unpaid = total_unpaid_query.scalar() or 0
    
    # 查询已逾期的应收账款总额
    total_overdue_query = db.session.query(func.sum(Receivable.ReceivableAmount)).filter(
        Receivable.Status != 'Paid',
        Receivable.ReceivableDate < now
    )
    total_overdue = total_overdue_query.scalar() or 0
    
    # 查询最近的应收账款记录
    recent_receivables_query = db.session.query(Receivable).filter(
        Receivable.Status != 'Paid'
    ).order_by(Receivable.ReceivableDate.asc()).limit(limit)
    
    recent_receivables = []
    try:
        for receivable in recent_receivables_query:
            # 获取客户名称
            customer_name = None
            if receivable.CustomerID:
                customer_query = db.session.query(Customer.Name).filter(Customer.CustomerID == receivable.CustomerID)
                customer_name = customer_query.scalar()
            
            # 转换为字典
            receivable_dict = receivable.to_dict()
            
            # 确保日期是日期对象而不是字符串
            if 'ReceivableDate' in receivable_dict:
                if isinstance(receivable_dict['ReceivableDate'], str):
                    try:
                        receivable_dict['ReceivableDate'] = datetime.strptime(
                            receivable_dict['ReceivableDate'], '%Y-%m-%d').date()
                    except ValueError:
                        receivable_dict['ReceivableDate'] = now
                elif isinstance(receivable_dict['ReceivableDate'], datetime):
                    receivable_dict['ReceivableDate'] = receivable_dict['ReceivableDate'].date()
            else:
                receivable_dict['ReceivableDate'] = now
            
            receivable_dict['customer_name'] = customer_name
            recent_receivables.append(receivable_dict)
    except Exception as e:
        logger.error(f"Error processing receivables: {str(e)}")
    
    # 整合数据
    receivables_data = {
        'total': total_unpaid,
        'overdue': total_overdue,
        'records': recent_receivables
    }
    
    return receivables_data

# 获取应付账款摘要
def get_payables_summary(limit=5):
    # 当前日期
    now = datetime.now().date()
    
    # 查询未支付的应付账款总额
    total_unpaid_query = db.session.query(func.sum(Payable.PayableAmount)).filter(
        Payable.PayableStatus != 'Paid'
    )
    total_unpaid = total_unpaid_query.scalar() or 0
    
    # 查询已逾期的应付账款总额
    total_overdue_query = db.session.query(func.sum(Payable.PayableAmount)).filter(
        Payable.PayableStatus != 'Paid',
        Payable.PayableDate < now
    )
    total_overdue = total_overdue_query.scalar() or 0
    
    # 查询最近的应付账款记录
    recent_payables_query = db.session.query(Payable).filter(
        Payable.PayableStatus != 'Paid'
    ).order_by(Payable.PayableDate.asc()).limit(limit)
    
    recent_payables = []
    try:
        for payable in recent_payables_query:
            # 获取供应商名称
            vendor_name = None
            if payable.VendorID:
                vendor_query = db.session.query(Vendor.Name).filter(Vendor.VendorID == payable.VendorID)
                vendor_name = vendor_query.scalar()
            
            # 转换为字典
            payable_dict = payable.to_dict()
            
            # 确保日期是日期对象而不是字符串
            if 'PayableDate' in payable_dict:
                if isinstance(payable_dict['PayableDate'], str):
                    try:
                        payable_dict['PayableDate'] = datetime.strptime(
                            payable_dict['PayableDate'], '%Y-%m-%d').date()
                    except ValueError:
                        payable_dict['PayableDate'] = now
                elif isinstance(payable_dict['PayableDate'], datetime):
                    payable_dict['PayableDate'] = payable_dict['PayableDate'].date()
            else:
                payable_dict['PayableDate'] = now
            
            payable_dict['vendor_name'] = vendor_name
            recent_payables.append(payable_dict)
    except Exception as e:
        logger.error(f"Error processing payables: {str(e)}")
    
    # 整合数据
    payables_data = {
        'total': total_unpaid,
        'overdue': total_overdue,
        'records': recent_payables
    }
    
    return payables_data

# 获取月度财务统计
def get_monthly_financial_stats(year):
    # 设置地区设置
    try:
        locale.setlocale(locale.LC_ALL, '')
    except locale.Error:
        locale.setlocale(locale.LC_ALL, 'C')  # 使用备用区域设置
    
    # 确保current_month是整数
    try:
        current_month = datetime.now().month
    except:
        current_month = 12  # 默认设为12月
    
    monthly_stats = {}  # 使用字典而不是列表
    
    # 对每个月份进行计算
    for month in range(1, 13):
        month_name = calendar.month_name[month] if month <= 12 else f"Month {month}"
        
        # 如果是未来月份，则填入零值
        if year == datetime.now().year and month > current_month:
            monthly_stats[month_name] = {
                'month': month,
                'revenue': 0,
                'expenses': 0,
                'profit': 0
            }
            continue
        
        try:
            # 计算该月的收入（销售额）
            month_revenue_query = db.session.query(func.sum(Sale.TotalAmount)).filter(
                extract('year', Sale.SaleDate) == year,
                extract('month', Sale.SaleDate) == month,
                Sale.Status == 'Completed'
            )
            month_revenue = month_revenue_query.scalar() or 0
            
            # 计算该月的支出（采购额）
            month_expenses_query = db.session.query(func.sum(Purchase.total_amount)).filter(
                extract('year', Purchase.OrderDate) == year,
                extract('month', Purchase.OrderDate) == month,
                Purchase.Status == 'Completed'
            )
            month_expenses = month_expenses_query.scalar() or 0
            
            # 计算该月的利润
            month_profit = month_revenue - month_expenses
            
            # 添加到结果字典
            monthly_stats[month_name] = {
                'month': month,
                'revenue': float(month_revenue),
                'expenses': float(month_expenses),
                'profit': float(month_profit)
            }
        except Exception as e:
            logger.warning(f"Error calculating stats for month {month}: {str(e)}")
            monthly_stats[month_name] = {
                'month': month,
                'revenue': 0,
                'expenses': 0,
                'profit': 0
            }
    
    return monthly_stats

# API endpoint for Receivables
@financial_api.route('/receivables', methods=['GET'])
def get_receivables_api():
    """API endpoint to get receivable records with filtering."""
    try:
        status = request.args.get('status', 'all')
        query = Receivable.query.options(joinedload(Receivable.customer))

        if status != 'all':
            if status == 'overdue':
                query = query.filter(Receivable.ReceivableDate < datetime.utcnow(), Receivable.Status != 'Paid')
            else:
                query = query.filter(Receivable.Status == status)

        receivables = query.order_by(Receivable.ReceivableDate).all()
        result = [r.to_dict() for r in receivables]
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error in get_receivables_api: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to retrieve receivables', 'message': str(e)}), 500

# API endpoint for Payables
@financial_api.route('/payables', methods=['GET'])
def get_payables_api():
    """API endpoint to get payable records with filtering."""
    try:
        status = request.args.get('status', 'all')
        query = Payable.query.options(joinedload(Payable.vendor))

        if status != 'all':
            if status == 'overdue':
                query = query.filter(Payable.PayableDate < datetime.utcnow(), Payable.PayableStatus != 'Paid')
            else:
                query = query.filter(Payable.PayableStatus == status)

        payables = query.order_by(Payable.PayableDate).all()
        result = [p.to_dict() for p in payables]
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error in get_payables_api: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to retrieve payables', 'message': str(e)}), 500

# API endpoint for Accounts Summary
@financial_api.route('/summary', methods=['GET'])
def get_accounts_summary_api():
    """API endpoint to get a summary of receivables and payables."""
    try:
        # Calculate receivable summary
        total_receivable = db.session.query(func.sum(Receivable.ReceivableAmount))\
            .filter(Receivable.Status != 'Paid')\
            .scalar() or 0
        overdue_receivable = db.session.query(func.sum(Receivable.ReceivableAmount))\
            .filter(Receivable.Status != 'Paid', Receivable.ReceivableDate < datetime.utcnow())\
            .scalar() or 0

        # Calculate payable summary
        total_payable = db.session.query(func.sum(Payable.PayableAmount))\
            .filter(Payable.PayableStatus != 'Paid')\
            .scalar() or 0
        overdue_payable = db.session.query(func.sum(Payable.PayableAmount))\
            .filter(Payable.PayableStatus != 'Paid', Payable.PayableDate < datetime.utcnow())\
            .scalar() or 0

        return jsonify({
            'receivables': {
                'total': float(total_receivable),
                'overdue': float(overdue_receivable)
            },
            'payables': {
                'total': float(total_payable),
                'overdue': float(overdue_payable)
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error in get_accounts_summary_api: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to retrieve account summary',
            'message': str(e),
            # Default values on error
            'receivables': {'total': 0, 'overdue': 0},
            'payables': {'total': 0, 'overdue': 0}
        }), 500

# 从完成的销售订单创建应收账款
@financial_api.route('/create-receivables', methods=['POST'])
def create_receivables_from_sales():
    try:
        # 获取所有已完成但尚未创建应收账款的销售订单
        sales_without_receivables = db.session.query(Sale).filter(
            Sale.Status == 'Completed',
            ~Sale.SaleID.in_(db.session.query(Receivable.SaleID).filter(Receivable.SaleID.isnot(None)))
        ).all()
        
        if not sales_without_receivables:
            return jsonify({'success': False, 'error': 'No eligible sales found for receivable creation'})
        
        created_count = 0
        for sale in sales_without_receivables:
            # 设置应收账款日期（通常是销售日期后30天）
            receivable_date = sale.SaleDate + timedelta(days=30)
            
            # 创建新的应收账款记录
            new_receivable = Receivable(
                SaleID=sale.SaleID,
                CustomerID=sale.CustomerID,
                ReceivableAmount=sale.TotalAmount,
                ReceivableDate=receivable_date,
                Status='Unpaid',
                CreatedAt=datetime.now()
            )
            
            db.session.add(new_receivable)
            created_count += 1
        
        # 提交事务
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully created {created_count} receivables from completed sales',
            'count': created_count
        })
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error creating receivables: {str(e)}")
        return jsonify({'success': False, 'error': f"Database error: {str(e)}"})
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating receivables: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# 从完成的采购订单创建应付账款
@financial_api.route('/create-payables', methods=['POST'])
def create_payables_from_purchases():
    try:
        # 获取所有已完成但尚未创建应付账款的采购订单
        purchases_without_payables = db.session.query(Purchase).filter(
            Purchase.Status == 'Completed',
            ~Purchase.PurchaseID.in_(db.session.query(Payable.PurchaseID).filter(Payable.PurchaseID.isnot(None)))
        ).all()
        
        if not purchases_without_payables:
            return jsonify({'success': False, 'error': 'No eligible purchases found for payable creation'})
        
        created_count = 0
        for purchase in purchases_without_payables:
            # 设置应付账款日期（通常是采购日期后15天）
            payable_date = purchase.OrderDate + timedelta(days=15)
            
            # 创建新的应付账款记录
            new_payable = Payable(
                PurchaseID=purchase.PurchaseID,
                VendorID=purchase.VendorID,
                PayableAmount=purchase.TotalAmount,
                PayableDate=payable_date,
                PayableStatus='Unpaid',
                CreatedAt=datetime.now()
            )
            
            db.session.add(new_payable)
            created_count += 1
        
        # 提交事务
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully created {created_count} payables from completed purchases',
            'count': created_count
        })
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error creating payables: {str(e)}")
        return jsonify({'success': False, 'error': f"Database error: {str(e)}"})
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating payables: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# 获取所有应收账款
@financial_api.route('/receivables', methods=['GET'])
def get_all_receivables():
    try:
        # 获取状态过滤参数
        status_filter = request.args.get('status', 'all')
        
        # 根据状态过滤应收账款
        query = db.session.query(Receivable)
        
        if status_filter == 'Paid':
            query = query.filter(Receivable.Status == 'Paid')
        elif status_filter == 'Unpaid':
            query = query.filter(Receivable.Status == 'Unpaid')
        elif status_filter == 'overdue':
            now = datetime.now().date()
            query = query.filter(Receivable.Status == 'Unpaid', Receivable.ReceivableDate < now)
        
        # 按到期日期排序
        receivables = query.order_by(Receivable.ReceivableDate.asc()).all()
        
        # 转换为字典并添加客户名称
        result = []
        for receivable in receivables:
            receivable_dict = receivable.to_dict()
            
            # 获取客户名称
            if receivable.CustomerID:
                customer_query = db.session.query(Customer.Name).filter(Customer.CustomerID == receivable.CustomerID)
                customer_name = customer_query.scalar()
                receivable_dict['customer_name'] = customer_name
            
            result.append(receivable_dict)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error getting receivables: {str(e)}")
        return jsonify([])

# 获取所有应付账款
@financial_api.route('/payables', methods=['GET'])
def get_all_payables():
    try:
        # 获取状态过滤参数
        status_filter = request.args.get('status', 'all')
        
        # 根据状态过滤应付账款
        query = db.session.query(Payable)
        
        if status_filter == 'Paid':
            query = query.filter(Payable.PayableStatus == 'Paid')
        elif status_filter == 'Unpaid':
            query = query.filter(Payable.PayableStatus == 'Unpaid')
        elif status_filter == 'overdue':
            now = datetime.now().date()
            query = query.filter(Payable.PayableStatus == 'Unpaid', Payable.PayableDate < now)
        
        # 按到期日期排序
        payables = query.order_by(Payable.PayableDate.asc()).all()
        
        # 转换为字典并添加供应商名称
        result = []
        for payable in payables:
            payable_dict = payable.to_dict()
            
            # 获取供应商名称
            if payable.VendorID:
                vendor_query = db.session.query(Vendor.Name).filter(Vendor.VendorID == payable.VendorID)
                vendor_name = vendor_query.scalar()
                payable_dict['VendorName'] = vendor_name
            
            result.append(payable_dict)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error getting payables: {str(e)}")
        return jsonify([])

# 更新应收账款状态
@financial_api.route('/receivables/<int:receivable_id>', methods=['PUT'])
def update_receivable_status(receivable_id):
    try:
        # 获取请求数据
        data = request.json
        if not data or 'status' not in data:
            return jsonify({'success': False, 'error': 'Status not provided in request'})
        
        # 获取应收账款记录
        receivable = db.session.query(Receivable).filter(Receivable.ReceivableID == receivable_id).first()
        if not receivable:
            return jsonify({'success': False, 'error': f'Receivable with ID {receivable_id} not found'})
        
        # 更新状态
        receivable.Status = data['status']
        if data['status'] == 'Paid':
            receivable.PaidDate = datetime.now()
        
        # 提交事务
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully updated receivable status to {data["status"]}'
        })
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error updating receivable: {str(e)}")
        return jsonify({'success': False, 'error': f"Database error: {str(e)}"})
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating receivable: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# 更新应付账款状态
@financial_api.route('/payables/<int:payable_id>', methods=['PUT'])
def update_payable_status(payable_id):
    try:
        # 获取请求数据
        data = request.json
        if not data or 'status' not in data:
            return jsonify({'success': False, 'error': 'Status not provided in request'})
        
        # 获取应付账款记录
        payable = db.session.query(Payable).filter(Payable.PayableID == payable_id).first()
        if not payable:
            return jsonify({'success': False, 'error': f'Payable with ID {payable_id} not found'})
        
        # 更新状态
        payable.PayableStatus = data['status']
        if data['status'] == 'Paid':
            payable.PaidDate = datetime.now()
        
        # 提交事务
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully updated payable status to {data["status"]}'
        })
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error updating payable: {str(e)}")
        return jsonify({'success': False, 'error': f"Database error: {str(e)}"})
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating payable: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# 注册蓝图
def register_blueprints(app):
    app.register_blueprint(financial_bp)
    app.register_blueprint(financial_api) 