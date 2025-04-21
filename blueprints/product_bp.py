from flask import Blueprint, render_template, request, jsonify, current_app
from models import db, Dish, SaleDish, Sale
from sqlalchemy import func
import os
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

# 创建两个Blueprint
product_bp = Blueprint('product_bp', __name__, template_folder='../templates')
product_api = Blueprint('product_api', __name__, url_prefix='/api/products')

@product_bp.route('/products')
def product_management():
    """渲染产品管理页面"""
    return render_template('product_management.html')

@product_api.route('', methods=['GET'])
def get_products():
    """获取所有产品"""
    try:
        category = request.args.get('category', '')
        search_term = request.args.get('search', '')
        
        # 构建查询
        query = Dish.query
        
        # 应用过滤条件
        if category:
            query = query.filter(Dish.Category == category)
        
        if search_term:
            query = query.filter(Dish.Name.ilike(f'%{search_term}%'))
        
        products = query.all()
        
        # 转换为JSON格式
        result = []
        for product in products:
            result.append({
                'id': product.DishID,
                'name': product.Name,
                'category': product.Category,
                'price': float(product.Price) if product.Price else 0.0,
                'stock': 0,  # 库存信息需另外查询
                'active': True,
                'image_url': product.ImageURL or 'default.jpg',
                'description': product.Description or ''
            })
        
        return jsonify(result)
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving products: {str(e)}")
        return jsonify({"success": False, "message": "获取产品失败"}), 500

@product_api.route('/categories', methods=['GET'])
def get_categories():
    """获取所有产品分类"""
    try:
        # 返回披萨店的固定分类（英文）
        categories = [
            {"id": "Pizza", "name": "Pizza"},
            {"id": "Sides", "name": "Sides"},
            {"id": "Salad", "name": "Salad"},
            {"id": "Drinks", "name": "Drinks"}
        ]
        
        return jsonify(categories)
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving categories: {str(e)}")
        return jsonify({"success": False, "message": "Failed to retrieve categories"}), 500

@product_api.route('/bestsellers', methods=['GET'])
def get_bestsellers():
    """获取热销商品数据，基于订单统计"""
    try:
        days = request.args.get('days', 30, type=int)
        limit = request.args.get('limit', 5, type=int)
        date_limit = datetime.now() - timedelta(days=days)
        
        # 基于订单数据计算热销商品
        query = db.session.query(
            Dish.DishID,
            Dish.Name,
            Dish.Category,
            func.count(SaleDish.SaleID).label('order_count'),
            func.sum(SaleDish.Quantity).label('total_quantity'),
            func.sum(SaleDish.Quantity * Dish.Price).label('total_revenue')
        ).join(
            SaleDish, Dish.DishID == SaleDish.DishID
        ).join(
            Sale, Sale.SaleID == SaleDish.SaleID
        ).filter(
            Sale.SaleDate >= date_limit,
            Sale.Status == 'Completed'  # 仅计算已完成的订单
        ).group_by(
            Dish.DishID, 
            Dish.Name,
            Dish.Category
        ).order_by(
            func.sum(SaleDish.Quantity).desc()
        ).limit(limit)
        
        bestsellers = query.all()
        
        # 处理结果
        result = [{
            'id': item.DishID,
            'name': item.Name,
            'category': item.Category,
            'order_count': item.order_count,
            'total_quantity': item.total_quantity,
            'total_revenue': float(item.total_revenue or 0)
        } for item in bestsellers]
        
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error retrieving bestsellers: {str(e)}")
        return jsonify({"success": False, "message": "Failed to retrieve bestselling products"}), 500

@product_api.route('/category-stats', methods=['GET'])
def get_category_stats():
    """获取按类别的销售统计，基于订单统计"""
    try:
        days = request.args.get('days', 30, type=int)
        date_limit = datetime.now() - timedelta(days=days)
        
        # 基于订单和分类统计
        query = db.session.query(
            Dish.Category,
            func.count(SaleDish.SaleID).label('order_count'),
            func.sum(SaleDish.Quantity).label('total_quantity'),
            func.sum(SaleDish.Quantity * Dish.Price).label('total_revenue')
        ).join(
            SaleDish, Dish.DishID == SaleDish.DishID
        ).join(
            Sale, Sale.SaleID == SaleDish.SaleID
        ).filter(
            Sale.SaleDate >= date_limit,
            Sale.Status == 'Completed'  # 仅计算已完成的订单
        ).group_by(
            Dish.Category
        )
        
        sales_data = query.all()
        
        # 计算总收入
        total_revenue = sum(float(item.total_revenue or 0) for item in sales_data)
        
        # 处理结果
        result = []
        for item in sales_data:
            category = item.Category if item.Category in ["Pizza", "Sides", "Salad", "Drinks"] else "Other"
            revenue = float(item.total_revenue or 0)
            percentage = (revenue / total_revenue * 100) if total_revenue > 0 else 0
            
            result.append({
                'category': category,
                'order_count': item.order_count,
                'total_quantity': item.total_quantity,
                'total_revenue': revenue,
                'percentage': percentage
            })
        
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error retrieving category stats: {str(e)}")
        return jsonify({"success": False, "message": "Failed to retrieve category statistics"}), 500

@product_api.route('', methods=['POST'])
def add_product():
    """添加新产品"""
    try:
        # 处理表单数据
        name = request.form.get('name')
        category = request.form.get('category')
        price = request.form.get('price')
        description = request.form.get('description', '')
        
        # 验证必填字段
        if not name or not price:
            return jsonify({'success': False, 'error': '名称和价格为必填项'}), 400
        
        # 创建新产品
        new_product = Dish(
            Name=name,
            Category=category,
            Price=price,
            Description=description,
            Status="Available"
        )
        
        # 处理图片上传
        if 'image' in request.files:
            file = request.files['image']
            if file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'static/img/dishes'), filename)
                file.save(file_path)
                new_product.ImageURL = filename
        
        db.session.add(new_product)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '产品添加成功'})
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding product: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@product_api.route('/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """更新产品信息"""
    try:
        product = Dish.query.get(product_id)
        
        if not product:
            return jsonify({'success': False, 'error': '产品不存在'}), 404
        
        # 更新基本信息
        if 'name' in request.form:
            product.Name = request.form.get('name')
        if 'category' in request.form:
            product.Category = request.form.get('category')
        if 'price' in request.form:
            product.Price = request.form.get('price')
        if 'description' in request.form:
            product.Description = request.form.get('description')
        if 'status' in request.form:
            product.Status = request.form.get('status')
        
        # 处理图片上传
        if 'image' in request.files:
            file = request.files['image']
            if file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'static/img/dishes'), filename)
                file.save(file_path)
                product.ImageURL = filename
        
        db.session.commit()
        return jsonify({'success': True, 'message': '产品更新成功'})
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating product: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@product_api.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """获取单个产品详情"""
    try:
        product = Dish.query.get(product_id)
        
        if not product:
            return jsonify({'error': '产品不存在'}), 404
        
        return jsonify({
            'id': product.DishID,
            'name': product.Name,
            'category': product.Category,
            'price': float(product.Price) if product.Price else 0.0,
            'description': product.Description or '',
            'status': product.Status,
            'image_url': product.ImageURL or 'default.jpg'
        })
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving product {product_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@product_api.route('/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """删除产品"""
    try:
        product = Dish.query.get(product_id)
        
        if not product:
            return jsonify({'success': False, 'error': '产品不存在'}), 404
        
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '产品删除成功'})
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting product {product_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@product_api.route('/export', methods=['GET'])
def export_products():
    """导出产品数据"""
    try:
        from flask import Response
        import csv
        import io
        
        # 查询所有产品
        products = Dish.query.all()
        
        # 创建CSV文件
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入标题行
        writer.writerow(['ID', 'Name', 'Category', 'Price', 'Description', 'Status', 'Image'])
        
        # 写入产品数据
        for product in products:
            writer.writerow([
                product.DishID,
                product.Name,
                product.Category,
                product.Price,
                product.Description,
                product.Status,
                product.ImageURL
            ])
        
        # 返回CSV文件
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=products.csv"}
        )
    
    except Exception as e:
        current_app.logger.error(f"Error exporting products: {str(e)}")
        return jsonify({'error': str(e)}), 500 