from flask import Blueprint, render_template, request, jsonify
from sqlalchemy import func
from models import db, Dish, DishIngredient

# 菜品页面蓝图
dishes_bp = Blueprint('dishes_bp', __name__, template_folder='../templates')

# 菜品API蓝图
dishes_api = Blueprint('dishes_api', __name__, url_prefix='/api/dishes')

@dishes_bp.route('/menu')
def menu():
    """渲染菜品菜单页面"""
    dishes = Dish.query.filter(Dish.Status == 'Available').all()
    categories = db.session.query(Dish.Category).distinct().all()
    return render_template('dishes/menu.html', dishes=dishes, categories=[cat[0] for cat in categories])

@dishes_api.route('/all', methods=['GET'])
def get_all_dishes():
    """获取所有可用菜品"""
    try:
        # 获取查询参数
        category = request.args.get('category', '')
        
        # 构建查询
        query = Dish.query.filter(Dish.Status == 'Available')
        
        # 按分类过滤
        if category:
            query = query.filter(Dish.Category == category)
        
        # 执行查询
        dishes = query.order_by(Dish.Name).all()
        
        # 转换为字典列表
        result = []
        for dish in dishes:
            dish_dict = {
                'DishID': dish.DishID,
                'Name': dish.Name,
                'Price': float(dish.Price),
                'discount_price': float(dish.discount_price) if dish.discount_price else None,
                'Category': dish.Category,
                'Description': dish.Description,
                'Status': dish.Status,
                'ImageURL': dish.ImageURL
            }
            result.append(dish_dict)
        
        return jsonify(result)
    except Exception as e:
        print(f"Error in get_all_dishes: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dishes_api.route('/<int:dish_id>', methods=['GET'])
def get_dish(dish_id):
    """获取特定菜品的详细信息"""
    try:
        dish = Dish.query.get_or_404(dish_id)
        
        # 获取菜品配料
        ingredients = db.session.query(
            DishIngredient.ItemID,
            DishIngredient.Quantity
        ).filter(DishIngredient.DishID == dish_id).all()
        
        # 构建响应
        result = {
            'DishID': dish.DishID,
            'Name': dish.Name,
            'Price': float(dish.Price),
            'discount_price': float(dish.discount_price) if dish.discount_price else None,
            'Category': dish.Category,
            'Description': dish.Description,
            'Status': dish.Status,
            'ImageURL': dish.ImageURL,
            'ingredients': [{'ItemID': item[0], 'Quantity': float(item[1])} for item in ingredients]
        }
        
        return jsonify(result)
    except Exception as e:
        print(f"Error in get_dish: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dishes_api.route('/categories', methods=['GET'])
def get_categories():
    """获取所有菜品分类"""
    try:
        categories = db.session.query(Dish.Category).distinct().all()
        return jsonify([cat[0] for cat in categories])
    except Exception as e:
        print(f"Error in get_categories: {str(e)}")
        return jsonify({'error': str(e)}), 500 