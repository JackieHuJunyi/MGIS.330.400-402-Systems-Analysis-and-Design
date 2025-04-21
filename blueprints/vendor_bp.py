# blueprints/vendor_bp.py
from flask import Blueprint, render_template, request, jsonify, current_app
# Ensure necessary models and libraries are imported
from models import db, Vendor, DeliveryPlatform, MaintenanceProvider, Payable, Purchase
from sqlalchemy import func
from datetime import datetime, timedelta
from decimal import Decimal # Import Decimal for precise amount handling
import logging # Import logging

# Setup logger
logger = logging.getLogger(__name__)

# Create Blueprints
vendor_bp = Blueprint('vendor_bp', __name__, template_folder='../templates')
vendor_api = Blueprint('vendor_api', __name__, url_prefix='/api/vendors')

@vendor_bp.route('/vendors/management')
def vendor_management():
    """Renders the vendor management page"""
    return render_template('vendor_management.html')

# ===================== Food Delivery Platform APIs (Keep Existing) =====================
# ... (Keep existing code for DeliveryPlatform APIs) ...

@vendor_api.route('/delivery-platforms', methods=['GET'])
def get_delivery_platforms():
    """获取所有送餐平台列表"""
    try:
        platforms = DeliveryPlatform.query.all()
        result = [platform.to_dict() for platform in platforms]
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"获取送餐平台列表出错: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@vendor_api.route('/delivery-platforms/<int:platform_id>', methods=['GET'])
def get_delivery_platform(platform_id):
    """获取特定送餐平台详情"""
    try:
        platform = DeliveryPlatform.query.get(platform_id)
        if not platform:
            return jsonify({"success": False, "message": "平台不存在"}), 404
        
        return jsonify({"success": True, "data": platform.to_dict()})
    except Exception as e:
        current_app.logger.error(f"获取送餐平台详情出错: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@vendor_api.route('/delivery-platforms', methods=['POST'])
def add_delivery_platform():
    """添加新送餐平台"""
    try:
        data = request.get_json()
        
        # 创建新平台
        new_platform = DeliveryPlatform(
            PlatformName=data.get('name'),
            ContactPerson=data.get('contact_person'),
            ContactPhone=data.get('contact_phone'),
            Email=data.get('email'),
            CommissionRate=data.get('commission_rate'),
            SettlementCycle=data.get('settlement_cycle'),
            CooperationStartDate=datetime.strptime(data.get('cooperation_start_date'), '%Y-%m-%d').date() if data.get('cooperation_start_date') else None,
            OrdersThisMonth=data.get('orders_this_month', 0),
            Status=data.get('status', 'Active'),
            Description=data.get('description')
        )
        
        db.session.add(new_platform)
        db.session.commit()
        
        return jsonify({"success": True, "message": "送餐平台添加成功", "data": new_platform.to_dict()})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"添加送餐平台出错: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@vendor_api.route('/delivery-platforms/<int:platform_id>', methods=['PUT'])
def update_delivery_platform(platform_id):
    """更新送餐平台信息"""
    try:
        platform = DeliveryPlatform.query.get(platform_id)
        if not platform:
            return jsonify({"success": False, "message": "平台不存在"}), 404
        
        data = request.get_json()
        
        # 更新平台信息
        if 'name' in data:
            platform.PlatformName = data['name']
        if 'contact_person' in data:
            platform.ContactPerson = data['contact_person']
        if 'contact_phone' in data:
            platform.ContactPhone = data['contact_phone']
        if 'email' in data:
            platform.Email = data['email']
        if 'commission_rate' in data:
            platform.CommissionRate = data['commission_rate']
        if 'settlement_cycle' in data:
            platform.SettlementCycle = data['settlement_cycle']
        if 'cooperation_start_date' in data and data['cooperation_start_date']:
            platform.CooperationStartDate = datetime.strptime(data['cooperation_start_date'], '%Y-%m-%d').date()
        if 'orders_this_month' in data:
            platform.OrdersThisMonth = data['orders_this_month']
        if 'status' in data:
            platform.Status = data['status']
        if 'description' in data:
            platform.Description = data['description']
        
        db.session.commit()
        
        return jsonify({"success": True, "message": "送餐平台更新成功", "data": platform.to_dict()})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新送餐平台出错: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@vendor_api.route('/delivery-platforms/<int:platform_id>', methods=['DELETE'])
def delete_delivery_platform(platform_id):
    """删除送餐平台"""
    try:
        platform = DeliveryPlatform.query.get(platform_id)
        if not platform:
            return jsonify({"success": False, "message": "平台不存在"}), 404
        
        db.session.delete(platform)
        db.session.commit()
        
        return jsonify({"success": True, "message": "送餐平台删除成功"})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除送餐平台出错: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===================== Maintenance Provider APIs (Keep Existing) =====================
# ... (Keep existing code for MaintenanceProvider APIs) ...
@vendor_api.route('/maintenance-providers', methods=['GET'])
def get_maintenance_providers():
    """获取所有设备维护服务提供商列表"""
    try:
        providers = MaintenanceProvider.query.all()
        result = [provider.to_dict() for provider in providers]
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"获取维护服务提供商列表出错: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@vendor_api.route('/maintenance-providers/<int:provider_id>', methods=['GET'])
def get_maintenance_provider(provider_id):
    """获取特定维护服务提供商详情"""
    try:
        provider = MaintenanceProvider.query.get(provider_id)
        if not provider:
            return jsonify({"success": False, "message": "服务提供商不存在"}), 404
        
        return jsonify({"success": True, "data": provider.to_dict()})
    except Exception as e:
        current_app.logger.error(f"获取维护服务提供商详情出错: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@vendor_api.route('/maintenance-providers', methods=['POST'])
def add_maintenance_provider():
    """添加新设备维护服务提供商"""
    try:
        data = request.get_json()
        
        # 创建新服务提供商
        new_provider = MaintenanceProvider(
            ProviderName=data.get('name'),
            ServiceType=data.get('service_type'),
            ContactPerson=data.get('contact_person'),
            ContactPhone=data.get('contact_phone'),
            Email=data.get('email'),
            ContractExpiryDate=datetime.strptime(data.get('contract_expiry_date'), '%Y-%m-%d').date() if data.get('contract_expiry_date') else None,
            LastServiceDate=datetime.strptime(data.get('last_service_date'), '%Y-%m-%d').date() if data.get('last_service_date') else None,
            NextServiceDate=datetime.strptime(data.get('next_service_date'), '%Y-%m-%d').date() if data.get('next_service_date') else None,
            MaintenanceCycle=data.get('maintenance_cycle'),
            Status=data.get('status', 'Active'),
            Description=data.get('description')
        )
        
        db.session.add(new_provider)
        db.session.commit()
        
        return jsonify({"success": True, "message": "维护服务提供商添加成功", "data": new_provider.to_dict()})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"添加维护服务提供商出错: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@vendor_api.route('/maintenance-providers/<int:provider_id>', methods=['PUT'])
def update_maintenance_provider(provider_id):
    """更新维护服务提供商信息"""
    try:
        provider = MaintenanceProvider.query.get(provider_id)
        if not provider:
            return jsonify({"success": False, "message": "服务提供商不存在"}), 404
        
        data = request.get_json()
        
        # 更新服务提供商信息
        if 'name' in data:
            provider.ProviderName = data['name']
        if 'service_type' in data:
            provider.ServiceType = data['service_type']
        if 'contact_person' in data:
            provider.ContactPerson = data['contact_person']
        if 'contact_phone' in data:
            provider.ContactPhone = data['contact_phone']
        if 'email' in data:
            provider.Email = data['email']
        if 'contract_expiry_date' in data and data['contract_expiry_date']:
            provider.ContractExpiryDate = datetime.strptime(data['contract_expiry_date'], '%Y-%m-%d').date()
        if 'last_service_date' in data and data['last_service_date']:
            provider.LastServiceDate = datetime.strptime(data['last_service_date'], '%Y-%m-%d').date()
        if 'next_service_date' in data and data['next_service_date']:
            provider.NextServiceDate = datetime.strptime(data['next_service_date'], '%Y-%m-%d').date()
        if 'maintenance_cycle' in data:
            provider.MaintenanceCycle = data['maintenance_cycle']
        if 'status' in data:
            provider.Status = data['status']
        if 'description' in data:
            provider.Description = data['description']
        
        db.session.commit()
        
        return jsonify({"success": True, "message": "维护服务提供商更新成功", "data": provider.to_dict()})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新维护服务提供商出错: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@vendor_api.route('/maintenance-providers/<int:provider_id>', methods=['DELETE'])
def delete_maintenance_provider(provider_id):
    """删除维护服务提供商"""
    try:
        provider = MaintenanceProvider.query.get(provider_id)
        if not provider:
            return jsonify({"success": False, "message": "服务提供商不存在"}), 404
        
        db.session.delete(provider)
        db.session.commit()
        
        return jsonify({"success": True, "message": "维护服务提供商删除成功"})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除维护服务提供商出错: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

# ===================== Food Vendor APIs (Keep Existing) =====================

@vendor_api.route('/food-vendors', methods=['GET'])
def get_food_vendors():
    """获取所有食品供应商列表"""
    try:
        vendors = Vendor.query.all()
        result = [vendor.to_dict() for vendor in vendors]
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"获取食品供应商列表出错: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@vendor_api.route('/food', methods=['GET'])
def get_food_vendors_alt():
    """获取所有食品供应商列表 (替代路径)"""
    return get_food_vendors()

@vendor_api.route('/food-vendors/<int:vendor_id>', methods=['GET'])
def get_food_vendor(vendor_id):
    """获取特定食品供应商详情"""
    try:
        vendor = Vendor.query.get(vendor_id)
        if not vendor:
            return jsonify({"success": False, "message": "供应商不存在"}), 404

        return jsonify(vendor.to_dict())
    except Exception as e:
        current_app.logger.error(f"获取食品供应商详情出错: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@vendor_api.route('/food/<int:vendor_id>', methods=['GET'])
def get_food_vendor_alt(vendor_id):
    """获取特定食品供应商详情 (替代路径)"""
    return get_food_vendor(vendor_id)

@vendor_api.route('/food-vendors', methods=['POST'])
def add_food_vendor():
    """添加新食品供应商"""
    try:
        data = request.get_json()

        # 创建新供应商
        new_vendor = Vendor(
            Name=data.get('Name'),
            ContactPerson=data.get('ContactPerson'),
            Phone=data.get('Phone'), # 使用模型中的 Phone 字段
            Email=data.get('Email'),
            Address=data.get('Address'),
            Description=data.get('Description'),
            Type='Food',  # 设置类型为食品供应商
            CreatedAt=datetime.now()
        )

        db.session.add(new_vendor)
        db.session.commit()

        return jsonify({"success": True, "message": "食品供应商添加成功", "data": new_vendor.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"添加食品供应商出错: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@vendor_api.route('/food', methods=['POST'])
def add_food_vendor_alt():
    """添加新食品供应商 (替代路径)"""
    return add_food_vendor()

@vendor_api.route('/food-vendors/<int:vendor_id>', methods=['PUT'])
def update_food_vendor(vendor_id):
    """更新食品供应商信息"""
    try:
        vendor = Vendor.query.get(vendor_id)
        if not vendor:
            return jsonify({"success": False, "message": "供应商不存在"}), 404

        data = request.get_json()

        # 更新供应商信息
        if 'Name' in data:
            vendor.Name = data['Name']
        if 'ContactPerson' in data:
            vendor.ContactPerson = data['ContactPerson']
        if 'Phone' in data:
            vendor.Phone = data['Phone'] # Use the correct field name from the model
        if 'Email' in data:
            vendor.Email = data['Email']
        if 'Address' in data:
            vendor.Address = data['Address']
        if 'Description' in data:
            vendor.Description = data['Description']

        # 设置更新时间
        vendor.UpdatedAt = datetime.now()

        db.session.commit()

        return jsonify({"success": True, "message": "食品供应商更新成功", "data": vendor.to_dict()})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新食品供应商出错: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@vendor_api.route('/food/<int:vendor_id>', methods=['PUT'])
def update_food_vendor_alt(vendor_id):
    """更新食品供应商信息 (替代路径)"""
    return update_food_vendor(vendor_id)

@vendor_api.route('/food-vendors/<int:vendor_id>', methods=['DELETE'])
def delete_food_vendor(vendor_id):
    """删除食品供应商"""
    try:
        vendor = Vendor.query.get(vendor_id)
        if not vendor:
            return jsonify({"success": False, "message": "供应商不存在"}), 404

        # Add check for related payables before deleting (optional but recommended)
        # related_payables = Payable.query.filter_by(VendorID=vendor_id).count()
        # if related_payables > 0:
        #    return jsonify({"success": False, "message": "Cannot delete vendor with existing payables."}), 400

        db.session.delete(vendor)
        db.session.commit()

        return jsonify({"success": True, "message": "食品供应商删除成功"})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除食品供应商出错: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@vendor_api.route('/food/<int:vendor_id>', methods=['DELETE'])
def delete_food_vendor_alt(vendor_id):
    """删除食品供应商 (替代路径)"""
    return delete_food_vendor(vendor_id)

# --- 新增: 创建应付款 API 端点 ---
@vendor_api.route('/<int:vendor_id>/payables', methods=['POST'])
def add_payable_for_vendor(vendor_id):
    """为指定供应商创建新的应付款记录"""
    # 检查供应商是否存在
    vendor = Vendor.query.get(vendor_id)
    if not vendor:
        logger.warning(f"Attempted to add payable for non-existent Vendor ID: {vendor_id}")
        return jsonify({"success": False, "message": "Vendor not found"}), 404

    data = request.get_json()
    if not data:
        logger.warning(f"Received empty payload for adding payable to Vendor ID: {vendor_id}")
        return jsonify({"success": False, "message": "No data provided"}), 400

    # 获取并验证数据
    amount_str = data.get('amount')
    due_date_str = data.get('due_date')
    purchase_id_str = data.get('purchase_id') # 可选

    # 基本验证
    if not amount_str or not due_date_str:
        logger.warning(f"Missing amount or due_date for payable creation (Vendor ID: {vendor_id})")
        return jsonify({"success": False, "message": "Amount and Due Date are required"}), 400

    try:
        payable_amount = Decimal(amount_str) # 使用 Decimal 处理金额
        if payable_amount <= 0:
             raise ValueError("Amount must be positive")
        # 尝试解析日期，允许 YYYY-MM-DD 格式
        payable_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError) as e:
        logger.error(f"Error parsing payable data for Vendor {vendor_id}: {e}", exc_info=True)
        return jsonify({"success": False, "message": f"Invalid data format: {e}"}), 400

    purchase_id = None
    if purchase_id_str:
        try:
            purchase_id = int(purchase_id_str)
            # 可选：检查 PurchaseID 是否存在
            # purchase_exists = Purchase.query.get(purchase_id)
            # if not purchase_exists:
            #     logger.warning(f"Purchase ID {purchase_id} not found when creating payable for Vendor {vendor_id}")
            #     return jsonify({"success": False, "message": f"Purchase ID {purchase_id} not found"}), 404
        except ValueError:
             logger.warning(f"Invalid Purchase ID format '{purchase_id_str}' for Vendor {vendor_id}")
             return jsonify({"success": False, "message": "Invalid Purchase ID format"}), 400

    # 创建新的 Payable 记录
    try:
        new_payable = Payable(
            VendorID=vendor_id,
            PayableAmount=payable_amount,
            PayableDate=payable_date, # Directly assign the date object
            PurchaseID=purchase_id,
            PayableStatus='Unpaid', # 默认状态
            CreatedAt=datetime.utcnow()
        )
        db.session.add(new_payable)
        db.session.commit()
        logger.info(f"Payable created successfully for Vendor {vendor_id}, Amount: {payable_amount}, Due: {payable_date}")
        # 返回创建的记录信息 (可选)
        created_payable_data = new_payable.to_dict() # Ensure to_dict handles date correctly
        return jsonify({"success": True, "message": "Payable created successfully", "data": created_payable_data}), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Database error creating payable for vendor {vendor_id}: {e}", exc_info=True)
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500
# --- 应付款创建 API 结束 ---