import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify
from sqlalchemy import or_, distinct
from sqlalchemy.exc import SQLAlchemyError
from models import Staff, db

# Logger
logger = logging.getLogger(__name__)

# Blueprints
staff_bp  = Blueprint('staff_page', __name__, url_prefix='/staff', template_folder='../templates')
staff_api = Blueprint('staff_api', __name__, url_prefix='/api/staff')

# ----- Page route -----
@staff_bp.route('/management')
def staff_management():
    """渲染员工管理页面"""
    logger.info("访问员工管理页面")
    return render_template('staff_management.html')


# ----- API routes -----

@staff_api.route('/all', methods=['GET'])
def get_all_staff():
    """获取所有员工数据，支持按 position + keyword 过滤"""
    try:
        position = request.args.get('position')
        keyword  = request.args.get('keyword')
        logger.debug(f"筛选条件: position={position}, keyword={keyword}")

        query = Staff.query
        if position and position != 'all':
            query = query.filter(Staff.position == position)
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(
                or_(
                    Staff.name.ilike(like),
                    Staff.phone.ilike(like),
                    Staff.email.ilike(like)
                )
            )

        staff_list = query.order_by(Staff.join_date.desc()).all()
        logger.info(f"找到 {len(staff_list)} 条员工记录")
        return jsonify(status="success", data=[s.to_dict() for s in staff_list])

    except Exception as e:
        logger.exception("获取员工列表失败")
        return jsonify(status="error", message=str(e)), 500


@staff_api.route('/positions', methods=['GET'])
def get_positions():
    """获取所有不同的 position 列表"""
    try:
        positions = (
            db.session.query(distinct(Staff.position))
            .filter(Staff.position.isnot(None))
            .all()
        )
        position_list = [p[0] for p in positions if p[0]]
        logger.info(f"找到 {len(position_list)} 个不同职位")
        return jsonify(status="success", data=position_list)

    except Exception as e:
        logger.exception("获取职位列表失败")
        return jsonify(status="error", message=str(e)), 500


@staff_api.route('/<int:staff_id>', methods=['GET'])
def get_staff(staff_id):
    """获取指定ID员工详情"""
    try:
        s = Staff.query.get(staff_id)
        if not s:
            logger.warning(f"员工ID {staff_id} 不存在")
            return jsonify(status="error", message=f"员工ID {staff_id} 不存在"), 404
        return jsonify(status="success", data=s.to_dict())

    except Exception as e:
        logger.exception("获取员工详情失败")
        return jsonify(status="error", message=str(e)), 500


@staff_api.route('', methods=['POST'])
def add_staff():
    """添加新员工"""
    try:
        data = request.get_json() or {}
        logger.debug(f"Received new staff data: {data}")

        # Required
        for f in ('name','position','phone'):
            if not data.get(f):
                return jsonify(status="error", message=f"缺少必要字段: {f}"), 400

        # Parse join_date
        jd = None
        if data.get('join_date'):
            try:
                jd = datetime.strptime(data['join_date'], '%Y-%m-%d')
            except ValueError as ve:
                return jsonify(status="error", message=f"日期格式错误: {ve}"), 400

        # Generate staff_code
        last = Staff.query.order_by(Staff.id.desc()).first()
        num  = int(last.staff_code.replace('ST','')) + 1 if last else 1
        code = f"ST{num:03d}"

        new = Staff(
            staff_code = code,
            name       = data['name'],
            position   = data['position'],
            department = data.get('department'),
            email      = data.get('email'),
            phone      = data['phone'],
            join_date  = jd,
            status     = data.get('status', 'Active'),
            address    = data.get('address'),
            performance= int(data.get('performance', 0))
        )
        db.session.add(new)
        db.session.commit()
        logger.info(f"添加员工成功 ID={new.id}")
        return jsonify(status="success", message="员工添加成功", data=new.to_dict()), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.exception("数据库错误")
        return jsonify(status="error", message=str(e)), 500


@staff_api.route('/<int:staff_id>', methods=['PUT'])
def update_staff(staff_id):
    """更新员工信息"""
    try:
        data = request.get_json() or {}
        logger.debug(f"Received update for {staff_id}: {data}")

        s = Staff.query.get(staff_id)
        if not s:
            return jsonify(status="error", message=f"员工ID {staff_id} 不存在"), 404

        # Parse join_date if present
        if data.get('join_date'):
            try:
                s.join_date = datetime.strptime(data['join_date'], '%Y-%m-%d')
            except ValueError as ve:
                return jsonify(status="error", message=f"日期格式错误: {ve}"), 400

        # Update fields
        for field, attr in (
            ('name','name'),
            ('position','position'),
            ('department','department'),
            ('email','email'),
            ('phone','phone'),
            ('status','status'),
            ('address','address'),
            ('performance','performance')
        ):
            if field in data:
                setattr(s, attr, data[field])

        db.session.commit()
        logger.info(f"更新员工 {staff_id} 成功")
        return jsonify(status="success", message="更新成功", data=s.to_dict())

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.exception("数据库错误")
        return jsonify(status="error", message=str(e)), 500


@staff_api.route('/<int:staff_id>', methods=['DELETE'])
def delete_staff(staff_id):
    """删除员工"""
    try:
        s = Staff.query.get(staff_id)
        if not s:
            return jsonify(status="error", message=f"员工ID {staff_id} 不存在"), 404

        db.session.delete(s)
        db.session.commit()
        logger.info(f"删除员工 {staff_id} 成功")
        return jsonify(status="success", message="员工删除成功")

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.exception("数据库错误")
        return jsonify(status="error", message=str(e)), 500