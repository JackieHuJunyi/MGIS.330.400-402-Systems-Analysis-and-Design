from flask import Blueprint, render_template, request, jsonify
from models import db, Item, Inventory, Vendor # Import necessary models and db
from datetime import datetime
from models import db, Inventory, BuyList   # <-- 新增 BuyList

# Blueprint for inventory pages
inventory_bp = Blueprint('inventory', __name__, template_folder='../templates')

# Blueprint for inventory APIs
inventory_api = Blueprint('inventory_api', __name__, url_prefix='/api/inventory')

# Inventory Management Page Route
@inventory_bp.route('/inventory')
def inventory_management():
    # Get query parameters, used for navigating from the item page
    item_id = request.args.get('item_id')
    # Pass item ID to the template if available
    return render_template('inventory.html', item_id=item_id)

# API to get all inventory records
@inventory_api.route('/all')
def get_all_inventory():
    try:
        # 改用连接查询获取库存数据
        inventory = Inventory.query.join(Item).all()
        inventory_list = [inv.to_dict() for inv in inventory]
        return jsonify(inventory_list)
    except Exception as e:
        # app.logger.error(f"Error fetching all inventory: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

# API to get low stock items
@inventory_api.route('/low_stock')
def get_low_stock():
    try:
        # 查询库存低于再订购水平的物品
        low_stock_items = Inventory.query.join(Item).filter(
            Inventory.StockLevel <= Inventory.ReorderLevel
        ).all()
        
        # 转换为字典列表
        low_stock_list = [item.to_dict() for item in low_stock_items]
        
        # 按库存水平排序 (库存量/再订购水平 越小越紧急)
        low_stock_list.sort(key=lambda x: (x['StockLevel'] / x['ReorderLevel']) if x['ReorderLevel'] > 0 else float('inf'))
        
        return jsonify(low_stock_list)
    except Exception as e:
        # app.logger.error(f"Error fetching low stock items: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

# API to update an inventory record
@inventory_api.route('/update', methods=['POST'])
def update_inventory():
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        # 检查库存ID
        inventory_id = data.get('inventory_id')
        if not inventory_id:
            return jsonify({"error": "Missing inventory_id"}), 400
            
        # 获取库存记录
        inventory = Inventory.query.get(inventory_id)
        if not inventory:
            return jsonify({"error": "Inventory item not found"}), 404
            
        # 更新库存信息
        if 'stock_level' in data:
            try:
                 inventory.StockLevel = float(data['stock_level'])
            except (ValueError, TypeError):
                 return jsonify({"error": "Invalid stock_level format"}), 400
        if 'reorder_level' in data:
             try:
                 inventory.ReorderLevel = float(data['reorder_level'])
             except (ValueError, TypeError):
                 return jsonify({"error": "Invalid reorder_level format"}), 400
        if 'vendor_id' in data:
             # 允许设置为空
             vendor_id_val = data.get('vendor_id')
             if vendor_id_val == '' or vendor_id_val is None:
                 inventory.VendorID = None
             else:
                 try:
                     inventory.VendorID = int(vendor_id_val)
                     # 可选：检查Vendor是否存在
                     if not Vendor.query.get(inventory.VendorID):
                         return jsonify({"error": f"Vendor with ID {inventory.VendorID} not found"}), 404
                 except (ValueError, TypeError):
                     return jsonify({"error": "Invalid vendor_id format"}), 400
            
        # 更新时间戳
        inventory.last_update = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            "message": "Inventory item updated successfully",
            "item": inventory.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        # app.logger.error(f"Error updating inventory {inventory_id}: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# API to add a new inventory record
@inventory_api.route('/add', methods=['POST'])
def add_inventory_item():
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        # 检查必要字段: item_id, stock_level, reorder_level
        required_fields = ['item_id', 'stock_level', 'reorder_level']
        for field in required_fields:
            if field not in data or data.get(field) is None:
                 return jsonify({"error": f"Missing required field: {field}"}), 400
        
        item_id = data['item_id']
        # 检查物品是否存在
        item = Item.query.get(item_id)
        if not item:
             return jsonify({"error": f"Item with ID {item_id} not found"}), 404
        
        # 检查该物品是否已有库存记录
        existing_inventory = Inventory.query.filter_by(ItemID=item.ItemID).first()
        if existing_inventory:
            return jsonify({"error": f"Item '{item.Name}' already exists in inventory"}), 400
            
        # 处理 vendor_id (非必须，但如果提供了要验证)
        vendor_id_val = data.get('vendor_id')
        vendor_id = None
        if vendor_id_val != '' and vendor_id_val is not None:
             try:
                 vendor_id = int(vendor_id_val)
                 # 检查Vendor是否存在
                 if not Vendor.query.get(vendor_id):
                      return jsonify({"error": f"Vendor with ID {vendor_id} not found"}), 404
             except (ValueError, TypeError):
                 return jsonify({"error": "Invalid vendor_id format"}), 400
        
        # 创建新库存记录
        try:
             stock_level = float(data['stock_level'])
             reorder_level = float(data['reorder_level'])
        except (ValueError, TypeError):
             return jsonify({"error": "Invalid number format for stock or reorder level"}), 400
             
        inventory = Inventory(
            ItemID=item.ItemID,
            StockLevel=stock_level,
            ReorderLevel=reorder_level,
            VendorID=vendor_id,
            last_update=datetime.now()
        )
        
        db.session.add(inventory)
        db.session.commit()
        
        # 返回创建的库存信息
        return jsonify({
            "message": "Inventory item added successfully",
            "item": inventory.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        # app.logger.error(f"Error adding inventory item: {str(e)}", exc_info=True)
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500

# API to record stock in (increase stock level for an existing item)
@inventory_api.route('/stock_in', methods=['POST'])
# def record_stock_in():
#     try:
#         data = request.get_json()
#         if not data:
#             return jsonify({"error": "No data provided"}), 400

#         item_id = data.get('item_id')
#         quantity_added = data.get('quantity_added')
#         # vendor_id = data.get('vendor_id') # Optional vendor tracking

#         if not item_id or quantity_added is None:
#             return jsonify({"error": "Missing required fields: item_id and quantity_added"}), 400

#         try:
#             item_id_int = int(item_id)
#             quantity_added_float = float(quantity_added)
#         except (ValueError, TypeError):
#             return jsonify({"error": "Invalid format for item_id or quantity_added"}), 400

#         if quantity_added_float <= 0:
#             return jsonify({"error": "Quantity added must be a positive number"}), 400

#         # Find the inventory record for the item
#         inventory = Inventory.query.filter_by(ItemID=item_id_int).first()

#         if not inventory:
#             # Check if the item itself exists, provide a more specific error
#             item_exists = Item.query.get(item_id_int)
#             if not item_exists:
#                  return jsonify({"error": f"Item with ID {item_id_int} not found."}), 404
#             else:
#                 # This case shouldn't happen if all items have inventory records initially
#                 # But good to handle just in case.
#                  return jsonify({"error": f"No inventory record found for item ID {item_id_int}. Cannot record stock-in."}), 404
       
#         # Update stock level
#         inventory.StockLevel += quantity_added_float
#         inventory.last_update = datetime.now()
#         # Optionally update last_purchase_date if applicable and data is provided
#         # if vendor_id:
#         #    inventory.VendorID = vendor_id # Update vendor if provided
#         #    inventory.last_purchase_date = datetime.now() # Or use a date from request

#         db.session.commit()

#         return jsonify({
#             "message": f"Successfully added {quantity_added_float} units to item ID {item_id_int}. New stock level: {inventory.StockLevel}",
#             "item": inventory.to_dict() # Return updated inventory item
#         })

#     except Exception as e:
#         db.session.rollback()
#         # app.logger.error(f"Error recording stock in for item {item_id}: {str(e)}", exc_info=True)
#         return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500
@inventory_api.route('/stock_in', methods=['POST'])
def stock_in():
    data = request.get_json() or {}
    item_id = data.get('item_id')
    qty     = data.get('quantity_added', 0)
    vendor_id = data.get('vendor_id')

    try:
        # 1) 更新库存
        inv = Inventory.query.filter_by(ItemID=item_id).first()
        if not inv:
            inv = Inventory(ItemID=item_id, StockLevel=0)
            db.session.add(inv)
            db.session.flush()  # 确保 inv.InventoryID 可用
        inv.StockLevel += qty
        inv.VendorID = vendor_id
        inv.last_purchase_date = datetime.utcnow()

        # 2) 同时把这次入库写到 buy_list 表
        buy_entry = BuyList(
            ItemID=item_id,
            InventoryQuantity=qty,
            VendorID=vendor_id
        )
        db.session.add(buy_entry)

        # 3) 一次性提交
        db.session.commit()
        return jsonify(inv.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
# API to get all vendors (used for inventory dropdown)
@inventory_api.route('/vendor')
def get_inventory_vendors():
    try:
        vendors = Vendor.query.all()
        return jsonify([vendor.to_dict() for vendor in vendors])
    except Exception as e:
        # app.logger.error(f"Error fetching vendors for inventory: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500 