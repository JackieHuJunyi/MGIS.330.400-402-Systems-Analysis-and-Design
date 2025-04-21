# blueprints/buy_list_bp.py

from flask import Blueprint, render_template, jsonify
from sqlalchemy.orm import joinedload
from models import db, BuyList, Item, Vendor

# —— 页面 Blueprint —— #
buy_list_bp = Blueprint(
    'buy_list_bp',
    __name__,
    template_folder='../templates',
    url_prefix='/inventory'
)

@buy_list_bp.route('/buy-list')
def buy_list_page():
    """
    渲染 Purchase Management 页面
    URL: GET /inventory/buy-list
    """
    return render_template('buy_list.html')


# —— API Blueprint —— #
buy_list_api = Blueprint(
    'buy_list_api',
    __name__,
    url_prefix='/api/buy-list'
)

@buy_list_api.route('', methods=['GET'])
def get_all_buy_list_items():
    """
    获取所有 buy_list 记录
    URL: GET /api/buy-list
    """
    try:
        items = (
            db.session.query(BuyList)
            .options(
                joinedload(BuyList.item),
                joinedload(BuyList.vendor)
            )
            .order_by(BuyList.PurchaseDate.desc())
            .all()
        )
        return jsonify([i.to_dict() for i in items])
    except Exception as e:
        print(f"[buy_list_api] Error: {e}")
        return jsonify({
            'error': 'Failed to retrieve buy list data',
            'details': str(e)
        }), 500