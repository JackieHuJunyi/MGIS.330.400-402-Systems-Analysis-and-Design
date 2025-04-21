from flask import Blueprint, render_template, request, jsonify
from models import db, Item, Inventory  # Import necessary models and db

# Blueprint for item pages
item_bp = Blueprint('item', __name__, template_folder='../templates') # Define template folder relative to blueprint file

# Blueprint for item APIs
item_api = Blueprint('item_api', __name__, url_prefix='/api/item')

# Item Management Page Route
@item_bp.route('/items')
def item_management():
    return render_template('item.html')

# API to get all items
@item_api.route('/all')
def get_all_items():
    try:
        # 获取所有物品
        items = Item.query.all()
        result = []
        
        for item in items:
            item_dict = item.to_dict()
            # 添加库存状态信息
            inventory = Inventory.query.filter_by(ItemID=item.ItemID).first()
            if inventory:
                item_dict['Status'] = 'Low' if inventory.StockLevel <= inventory.ReorderLevel else 'Normal'
                item_dict['InventoryID'] = inventory.InventoryID # 添加库存ID供前端使用
            else:
                item_dict['Status'] = 'None'  # 没有库存记录
                item_dict['InventoryID'] = None
                
            result.append(item_dict)
            
        return jsonify(result)
    except Exception as e:
        # Consider logging the error
        # app.logger.error(f"Error fetching all items: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

# API to add a new item
@item_api.route('/add', methods=['POST'])
def add_item():
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        # 检查必要字段
        if 'name' not in data or not data['name']:
            return jsonify({"error": "Missing required field: name"}), 400
        
        # 检查物品是否已存在
        existing_item = Item.query.filter_by(Name=data['name']).first()
        if existing_item:
            return jsonify({"error": f"Item name '{data['name']}' already exists"}), 400
            
        # 创建新物品
        item = Item(
            Name=data['name'],
            Category=data.get('category', ''),
            Description=data.get('description', ''),
            DefaultUnit=data.get('unit', '个')
        )
        
        db.session.add(item)
        db.session.commit()
        
        # 返回创建的物品信息
        return jsonify({
            "message": "Item added successfully",
            "item": item.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        # Consider logging the error
        # app.logger.error(f"Error adding item: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# API to update an existing item
@item_api.route('/update', methods=['POST'])
def update_item():
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        # 检查物品ID
        item_id = data.get('item_id')
        if not item_id:
            return jsonify({"error": "Missing item_id"}), 400
            
        # 获取物品记录
        item = Item.query.get(item_id)
        if not item:
            return jsonify({"error": "Item not found"}), 404
            
        # 更新物品信息
        if 'name' in data and data['name']:
            # 检查名称是否与其他物品冲突
            existing = Item.query.filter(Item.Name == data['name'], Item.ItemID != item_id).first()
            if existing:
                return jsonify({"error": f"Item name '{data['name']}' is already in use"}), 400
                
            item.Name = data['name']
            
        if 'category' in data:
            item.Category = data['category']
        if 'description' in data:
            item.Description = data['description']
        if 'unit' in data:
            item.DefaultUnit = data['unit']
            
        db.session.commit()
        
        return jsonify({
            "message": "Item updated successfully",
            "item": item.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        # Consider logging the error
        # app.logger.error(f"Error updating item {item_id}: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# API to get distinct item categories
@item_api.route('/category')
def get_item_categories():
    try:
        # 获取所有唯一的物品类别
        categories = db.session.query(Item.Category).distinct().all()
        categories = [c[0] for c in categories if c[0]]  # 过滤空类别
        
        return jsonify(categories)
    except Exception as e:
        # Consider logging the error
        # app.logger.error(f"Error fetching item categories: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500 