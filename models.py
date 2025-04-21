# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, date
from sqlalchemy import func
from decimal import Decimal # Ensure Decimal is imported
from sqlalchemy.orm import relationship
# 替代relativedelta函数
def _relativedelta(dt1, dt2):
    years = dt1.year - dt2.year
    # 如果当前月日小于生日月日，则年龄减1
    if (dt1.month, dt1.day) < (dt2.month, dt2.day):
        years -= 1
    return type('obj', (object,), {'years': years})

# 尝试导入dateutil
try:
    from dateutil.relativedelta import relativedelta
except ImportError:
    # 如果找不到dateutil，使用替代函数
    relativedelta = _relativedelta

# 初始化数据库对象，但不绑定到应用
db = SQLAlchemy()

# 菜品模型
class Dish(db.Model):
    __tablename__ = 'dish'
    DishID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100), nullable=False)
    # Use Decimal for prices to avoid floating point issues
    Price = db.Column(db.Numeric(10, 2), nullable=False)
    discount_price = db.Column(db.Numeric(10, 2), nullable=True)
    Category = db.Column(db.String(50))
    Description = db.Column(db.Text)
    Status = db.Column(db.String(20), default='Available')
    ImageURL = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    sale_items = db.relationship('SaleDish', backref='dish', lazy=True)
    # 新增与原料的关系
    ingredients = db.relationship('DishIngredient', backref='dish', lazy=True)

    def to_dict(self):
        return {
            'DishID': self.DishID,
            'Name': self.Name,
            'Price': float(self.Price) if self.Price else 0.0, # Convert Decimal to float for JSON
            'discount_price': float(self.discount_price) if self.discount_price else None,
            'Category': self.Category,
            'Description': self.Description,
            'Status': self.Status,
            'ImageURL': self.ImageURL,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

# 物品模型（基础商品）
class Item(db.Model):
    __tablename__ = 'item'
    ItemID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100), nullable=False)
    Category = db.Column(db.String(50))
    Description = db.Column(db.Text)
    DefaultUnit = db.Column(db.String(20), default='个')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    inventory = db.relationship('Inventory', backref='item', uselist=False)
    purchase_items = db.relationship('PurchaseItem', backref='item', lazy=True)
    # Relationship with DishIngredient
    dish_ingredients = db.relationship('DishIngredient', backref='item_details', lazy=True)


    def to_dict(self):
        current_stock = self.inventory.StockLevel if self.inventory else 0
        return {
            'ItemID': self.ItemID,
            'Name': self.Name,
            'Category': self.Category or '',
            'Description': self.Description or '',
            'DefaultUnit': self.DefaultUnit,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'CurrentStock': current_stock # Include stock level
        }
class BuyList(db.Model):
    __tablename__ = 'buy_list' # Table name in the database
    BuyListID = db.Column(db.Integer, primary_key=True)
    ItemID = db.Column(db.Integer, db.ForeignKey('item.ItemID'), nullable=False)
    InventoryQuantity = db.Column(db.Float, nullable=False)
    VendorID = db.Column(db.Integer, db.ForeignKey('vendor.VendorID'), nullable=False)
    PurchaseDate = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships to easily access related data
    item = relationship("Item") # Relationship to the Item model
    vendor = relationship("Vendor") # Relationship to the Vendor model

    def to_dict(self):
        """Converts the BuyList object to a dictionary."""
        return {
            'BuyListID': self.BuyListID,
            'ItemID': self.ItemID,
            'InventoryName': self.item.Name if self.item else 'Unknown Item', # Get name via relationship
            'InventoryQuantity': self.InventoryQuantity,
            'ItemUnit': self.item.DefaultUnit if self.item else 'unit', # Get unit via relationship
            'VendorID': self.VendorID,
            'SupplierName': self.vendor.Name if self.vendor else 'Unknown Vendor', # Get name via relationship
            'PurchaseDate': self.PurchaseDate.strftime('%Y-%m-%d %H:%M:%S') if self.PurchaseDate else None
        }


# 库存模型
class Inventory(db.Model):
    __tablename__ = 'inventory'
    InventoryID = db.Column(db.Integer, primary_key=True)
    ItemID = db.Column(db.Integer, db.ForeignKey('item.ItemID'), nullable=False)
    StockLevel = db.Column(db.Float, default=0)
    ReorderLevel = db.Column(db.Float, default=10)
    last_purchase_date = db.Column(db.DateTime)
    last_update = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    VendorID = db.Column(db.Integer, db.ForeignKey('vendor.VendorID'))

    # Relationships
    vendor = db.relationship('Vendor', backref='inventory_items')
    # No direct backref needed from Item to Inventory, handled by item relationship in Item model

    def to_dict(self):
        # 计算库存状态
        status = 'Normal'
        # Ensure ReorderLevel is not None before comparison
        if self.ReorderLevel is not None and self.StockLevel <= self.ReorderLevel:
            status = 'Low'

        return {
            'InventoryID': self.InventoryID,
            'ItemID': self.ItemID,
            'ItemName': self.item.Name if hasattr(self, 'item') and self.item else 'N/A', # Check if item exists
            'Category': self.item.Category if hasattr(self, 'item') and self.item else '',
            'StockLevel': self.StockLevel,
            'Unit': self.item.DefaultUnit if hasattr(self, 'item') and self.item else '',
            'ReorderLevel': self.ReorderLevel,
            'Status': status,
            'VendorID': self.VendorID,
            'SupplierName': self.vendor.Name if self.vendor else 'N/A',
            'LastPurchase': self.last_purchase_date.strftime('%Y-%m-%d') if self.last_purchase_date else None,
            'LastUpdate': self.last_update.strftime('%Y-%m-%d %H:%M:%S') if self.last_update else None
        }


# 菜品原料关系
class DishIngredient(db.Model):
    __tablename__ = 'dish_ingredient'
    DishIngredientID = db.Column(db.Integer, primary_key=True)
    DishID = db.Column(db.Integer, db.ForeignKey('dish.DishID'), nullable=False)
    ItemID = db.Column(db.Integer, db.ForeignKey('item.ItemID'), nullable=False)
    Quantity = db.Column(db.Float, nullable=False) # Amount of item per dish

    # Relationship (backref already defined in Dish and Item)
    # item = db.relationship('Item', backref='dish_uses')

    def to_dict(self):
        return {
            'DishIngredientID': self.DishIngredientID,
            'DishID': self.DishID,
            'DishName': self.dish.Name if self.dish else 'Unknown',
            'ItemID': self.ItemID,
            'ItemName': self.item_details.Name if self.item_details else 'Unknown',
            'Quantity': self.Quantity,
            'Unit': self.item_details.DefaultUnit if self.item_details else 'unit'
        }


# 供应商模型
class Vendor(db.Model):
    __tablename__ = 'vendor'
    VendorID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100), nullable=False)
    ContactPerson = db.Column(db.String(50))
    PhoneNum = db.Column(db.String(20)) # Consistent naming
    Email = db.Column(db.String(100))
    Address = db.Column(db.String(255))
    Phone = db.Column(db.String(20)) # Keep for backward compatibility if needed? Or remove?
    Type = db.Column(db.String(50), default='Food') # e.g., Food, Maintenance, Delivery
    Description = db.Column(db.Text)
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)
    UpdatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # 'created_at' is redundant with CreatedAt

    # Relationships
    purchases = db.relationship('Purchase', backref='vendor', lazy=True)
    payables = db.relationship('Payable', backref='vendor', lazy=True)
    # inventory_items relationship defined in Inventory model

    def to_dict(self):
        return {
            'VendorID': self.VendorID,
            'Name': self.Name,
            'ContactPerson': self.ContactPerson,
            'Phone': self.PhoneNum or self.Phone, # Prioritize PhoneNum
            'Email': self.Email,
            'Address': self.Address,
            'Type': self.Type,
            'Description': self.Description,
            'CreatedAt': self.CreatedAt.strftime('%Y-%m-%d %H:%M:%S') if self.CreatedAt else None,
            'UpdatedAt': self.UpdatedAt.strftime('%Y-%m-%d %H:%M:%S') if self.UpdatedAt else None,
            # Simpler aliases for consistency
            'id': self.VendorID,
            'name': self.Name,
            'contact_person': self.ContactPerson,
            'phone': self.PhoneNum or self.Phone,
            'email': self.Email,
            'address': self.Address,
            'created_at': self.CreatedAt.strftime('%Y-%m-%d %H:%M:%S') if self.CreatedAt else None
        }

# 采购模型
class Purchase(db.Model):
    __tablename__ = 'purchase'
    PurchaseID = db.Column(db.Integer, primary_key=True)
    OrderDate = db.Column(db.DateTime, default=datetime.utcnow)
    DeliveryDate = db.Column(db.DateTime, nullable=True) # Can be null initially
    Status = db.Column(db.String(20), default='Pending') # Pending, Completed, Cancelled
    VendorID = db.Column(db.Integer, db.ForeignKey('vendor.VendorID'))
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=True)
    total_amount = db.Column(db.Numeric(10, 2), default=0.00) # Use Numeric
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    items = db.relationship('PurchaseItem', backref='purchase', cascade='all, delete-orphan', lazy=True)
    staff = db.relationship('Staff', backref='purchases')
    payable = db.relationship('Payable', backref='purchase', uselist=False)

    def to_dict(self):
        return {
            'PurchaseID': self.PurchaseID,
            'OrderDate': self.OrderDate.strftime('%Y-%m-%d %H:%M:%S') if self.OrderDate else None,
            'DeliveryDate': self.DeliveryDate.strftime('%Y-%m-%d') if self.DeliveryDate else None,
            'Status': self.Status,
            'VendorID': self.VendorID,
            'VendorName': self.vendor.Name if self.vendor else None,
            'staff_id': self.staff_id,
            'staff_name': self.staff.name if self.staff else None,
            'total_amount': float(self.total_amount) if self.total_amount else 0.0,
            'notes': self.notes,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'items': [item.to_dict() for item in self.items] if self.items else []
        }

# 采购项目模型
class PurchaseItem(db.Model):
    __tablename__ = 'purchase_item'
    PurchaseItemID = db.Column(db.Integer, primary_key=True)
    PurchaseID = db.Column(db.Integer, db.ForeignKey('purchase.PurchaseID'), nullable=False)
    ItemID = db.Column(db.Integer, db.ForeignKey('item.ItemID'), nullable=False)
    Quantity = db.Column(db.Float, nullable=False)
    UnitPrice = db.Column(db.Numeric(10, 2)) # Use Numeric
    total_price = db.Column(db.Numeric(10, 2)) # Use Numeric
    received_quantity = db.Column(db.Float, default=0)
    received_date = db.Column(db.DateTime, nullable=True)

    # Relationship (backref defined in Item)
    # item = db.relationship('Item', backref='purchase_items')

    def to_dict(self):
        # Access item details via the relationship from PurchaseItem to Item
        item_name = self.item.Name if hasattr(self, 'item') and self.item else "Unknown"
        unit = self.item.DefaultUnit if hasattr(self, 'item') and self.item else ""

        return {
            'PurchaseItemID': self.PurchaseItemID,
            'PurchaseID': self.PurchaseID,
            'ItemID': self.ItemID,
            'ItemName': item_name,
            'Quantity': self.Quantity,
            'ReceivedQuantity': self.received_quantity,
            'Unit': unit,
            'UnitPrice': float(self.UnitPrice) if self.UnitPrice else None,
            'TotalPrice': float(self.total_price) if self.total_price else None,
            'ReceivedDate': self.received_date.strftime('%Y-%m-%d') if self.received_date else None
        }

# 销售模型
class Sale(db.Model):
    __tablename__ = 'sale'
    SaleID = db.Column(db.Integer, primary_key=True)
    SaleDate = db.Column(db.DateTime, default=datetime.utcnow)
    TotalAmount = db.Column(db.Numeric(10, 2), default=0.00) # Use Numeric
    DiscountAmount = db.Column(db.Numeric(10, 2), default=0.00) # Use Numeric
    Status = db.Column(db.String(20)) # e.g., Pending, Processing, Delivered, Completed, Cancelled
    OrderType = db.Column(db.String(20)) # e.g., Dine-in, Takeaway, Delivery
    Channel = db.Column(db.String(20)) # e.g., Web, App, Phone, Counter
    CustomerID = db.Column(db.Integer, db.ForeignKey('customer.CustomerID'), nullable=True) # Allow guest orders

    # --- 确认此字段存在 ---
    PaymentCompleted = db.Column(db.Boolean, default=False, nullable=False)
    # ---------------

    # Relationships
    items = db.relationship('SaleDish', backref='sale', lazy=True)
    customer = db.relationship('Customer', backref='sales', lazy=True)
    feedback = db.relationship('Feedback', backref='sale', lazy=True)
    receivable = db.relationship('Receivable', backref='sale', uselist=False)

    def to_dict(self):
        # Calculate discount based on actual items if DiscountAmount is null/zero
        calculated_discount = Decimal(0)
        if self.DiscountAmount is None or self.DiscountAmount == 0:
            calculated_discount = sum(
                ((item.dish.Price or Decimal(0)) - (item.dish.discount_price or item.dish.Price or Decimal(0))) * Decimal(item.Quantity)
                for item in self.items
                if item.dish and item.dish.discount_price is not None
            )

        sale_items = []
        if self.items:
            for item in self.items:
                # Ensure UnitPrice exists before calculation
                unit_price_val = item.UnitPrice if item.UnitPrice is not None else Decimal(0)
                quantity_val = item.Quantity if item.Quantity is not None else 0
                subtotal_val = unit_price_val * Decimal(quantity_val)

                sale_items.append({
                    'DishID': item.DishID,
                    'Name': item.dish.Name if item.dish else 'Unknown',
                    'Quantity': quantity_val,
                    'UnitPrice': float(unit_price_val), # Convert to float for JSON
                    'Subtotal': float(subtotal_val) # Convert to float for JSON
                })

        customer_info = None
        if self.customer:
            customer_info = {
                'CustomerID': self.customer.CustomerID,
                'Name': self.customer.Name,
                'PhoneNum': self.customer.PhoneNum,
                'MemLevel': self.customer.MemLevel
            }

        return {
            'SaleID': self.SaleID,
            'SaleDate': self.SaleDate.strftime('%Y-%m-%d %H:%M:%S') if self.SaleDate else None,
            'TotalAmount': float(self.TotalAmount) if self.TotalAmount else 0.0,
            'DiscountAmount': float(self.DiscountAmount if self.DiscountAmount is not None else calculated_discount),
            'Status': self.Status,
            'OrderType': self.OrderType,
            'Channel': self.Channel,
            'CustomerID': self.CustomerID,
            'CustomerName': self.customer.Name if self.customer else 'Guest',
            'items': sale_items,
            'customer': customer_info,
            'PaymentCompleted': self.PaymentCompleted # Include in response
        }

# 销售菜品模型
class SaleDish(db.Model):
    __tablename__ = 'sale_dish'
    SaleDishID = db.Column(db.Integer, primary_key=True)
    SaleID = db.Column(db.Integer, db.ForeignKey('sale.SaleID'), nullable=False)
    DishID = db.Column(db.Integer, db.ForeignKey('dish.DishID'), nullable=False)
    Quantity = db.Column(db.Integer, default=1)
    UnitPrice = db.Column(db.Numeric(10, 2), nullable=False) # Use Numeric

    # Relationship (backref defined in Dish)
    # dish = db.relationship('Dish', backref='sale_items')

    def to_dict(self):
        # Ensure UnitPrice and Quantity exist before calculation
        unit_price_val = self.UnitPrice if self.UnitPrice is not None else Decimal(0)
        quantity_val = self.Quantity if self.Quantity is not None else 0
        subtotal_val = unit_price_val * Decimal(quantity_val)

        return {
            'SaleDishID': self.SaleDishID,
            'SaleID': self.SaleID,
            'DishID': self.DishID,
            'DishName': self.dish.Name if self.dish else 'Unknown',
            'Quantity': quantity_val,
            'UnitPrice': float(unit_price_val), # Convert to float for JSON
            'Subtotal': float(subtotal_val) # Convert to float for JSON
        }

# 客户模型
class Customer(db.Model):
    __tablename__ = 'customer'
    CustomerID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100), nullable=False)
    BirthDate = db.Column(db.Date, nullable=True)
    PhoneNum = db.Column(db.String(20), unique=True)
    Email = db.Column(db.String(100))
    MemLevel = db.Column(db.String(20), default='Regular') # Bronze, Silver, Gold, Regular
    RegDate = db.Column(db.DateTime, default=datetime.utcnow)
    last_visit = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    # sales relationship defined in Sale model
    feedback = db.relationship('Feedback', backref='customer', lazy=True)
    receivables = db.relationship('Receivable', backref='customer', lazy=True)

    def to_dict(self):
        inactive_days = (datetime.utcnow() - self.last_visit).days if self.last_visit else None
        # Correctly count sales using the backref
        total_orders = len([sale for sale in self.sales if sale.Status == 'Completed'])

        # Calculate age if birthdate is provided
        age = None
        if self.BirthDate:
            today = date.today()
            age = today.year - self.BirthDate.year - ((today.month, today.day) < (self.BirthDate.month, self.BirthDate.day))

        return {
            'CustomerID': self.CustomerID,
            'Name': self.Name,
            'BirthDate': self.BirthDate.strftime('%Y-%m-%d') if self.BirthDate else None,
            'Age': age,
            'PhoneNum': self.PhoneNum,
            'Email': self.Email,
            'MemLevel': self.MemLevel,
            'RegDate': self.RegDate.strftime('%Y-%m-%d') if self.RegDate else None,
            'last_visit': self.last_visit.strftime('%Y-%m-%d %H:%M:%S') if self.last_visit else None,
            'TotalOrder': total_orders,
            'InactiveDay': inactive_days
        }


# 员工模型
class Staff(db.Model):
    __tablename__ = 'staff'
    id = db.Column(db.Integer, primary_key=True)
    staff_code = db.Column(db.String(10), unique=True, nullable=False)  # e.g. 'ST001'
    name       = db.Column(db.String(100), nullable=False)
    position   = db.Column(db.String(50))
    department = db.Column(db.String(50))
    email      = db.Column(db.String(100))
    phone      = db.Column(db.String(20))
    join_date  = db.Column(db.DateTime)
    status     = db.Column(db.String(20), default='Active') # Active, On Leave, Inactive
    address    = db.Column(db.String(255))
    performance= db.Column(db.Integer, default=0) # Example performance metric
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship (backref defined in Purchase)
    # purchases = db.relationship('Purchase', backref='staff')

    def to_dict(self):
        return {
            'id':          self.id,
            'staff_code':  self.staff_code,
            'name':        self.name,
            'position':    self.position,
            'department':  self.department,
            'email':       self.email,
            'phone':       self.phone,
            'join_date':   self.join_date.strftime('%Y-%m-%d') if self.join_date else None,
            'status':      self.status,
            'address':     self.address,
            'performance': self.performance,
            'created_at':  self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
# 反馈模型
class Feedback(db.Model):
    __tablename__ = 'feedback'
    FeedbackID = db.Column(db.Integer, primary_key=True)
    Rating = db.Column(db.Integer) # 1-5 stars
    Comment = db.Column(db.Text)
    CreateTime = db.Column(db.DateTime, default=datetime.utcnow)
    CustomerID = db.Column(db.Integer, db.ForeignKey('customer.CustomerID'), nullable=True) # Allow anonymous feedback
    SaleID = db.Column(db.Integer, db.ForeignKey('sale.SaleID'), nullable=True) # Link to specific sale if possible
    # Feedback status, e.g., New, Viewed, Addressed
    Status = db.Column(db.String(20), default='New')

    # Relationship (backrefs defined in Customer and Sale)
    # customer = db.relationship('Customer', backref='feedback')
    # sale = db.relationship('Sale', backref='feedback')

    def to_dict(self):
        return {
            'FeedbackID': self.FeedbackID,
            'Rating': self.Rating,
            'Comment': self.Comment,
            'CreateTime': self.CreateTime.strftime('%Y-%m-%d %H:%M:%S') if self.CreateTime else None,
            'CustomerID': self.CustomerID,
            'CustomerName': self.customer.Name if self.customer else 'Anonymous',
            'SaleID': self.SaleID,
            'Status': self.Status # Include feedback status
        }

# 应付款模型
class Payable(db.Model):
    __tablename__ = 'payable'
    PayableID = db.Column(db.Integer, primary_key=True)
    PayableStatus = db.Column(db.String(20), default='Unpaid') # Unpaid, Paid, Overdue
    PayableDate = db.Column(db.DateTime) # Due date
    PayableAmount = db.Column(db.Numeric(10, 2)) # Use Numeric
    PurchaseID = db.Column(db.Integer, db.ForeignKey('purchase.PurchaseID'), nullable=True) # Can be non-purchase related
    VendorID = db.Column(db.Integer, db.ForeignKey('vendor.VendorID'))
    PaidDate = db.Column(db.DateTime, nullable=True) # Actual payment date
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship (backrefs defined in Purchase and Vendor)
    # purchase = db.relationship('Purchase', backref='payable')
    # vendor = db.relationship('Vendor', backref='payables')

    def to_dict(self):
        return {
            'PayableID': self.PayableID,
            'PayableStatus': self.PayableStatus,
            'PayableDate': self.PayableDate.strftime('%Y-%m-%d') if self.PayableDate else None,
            'PayableAmount': float(self.PayableAmount) if self.PayableAmount else 0.0,
            'PurchaseID': self.PurchaseID,
            'VendorID': self.VendorID,
            'VendorName': self.vendor.Name if self.vendor else 'Unknown',
            'PaidDate': self.PaidDate.strftime('%Y-%m-%d') if self.PaidDate else None, # Include PaidDate
            'CreatedAt': self.CreatedAt.strftime('%Y-%m-%d %H:%M:%S') if self.CreatedAt else None # Include CreatedAt
        }


# 应收款模型
class Receivable(db.Model):
    __tablename__ = 'receivable'
    ReceivableID = db.Column(db.Integer, primary_key=True)
    ReceivableDate = db.Column(db.DateTime, nullable=False) # Due date
    Status = db.Column(db.String(20), default='Unpaid') # Unpaid, Paid, Overdue, Cancelled
    ReceivableAmount = db.Column(db.Numeric(10, 2), nullable=False) # Use Numeric
    SaleID = db.Column(db.Integer, db.ForeignKey('sale.SaleID'), nullable=False) # Must be linked to a sale
    CustomerID = db.Column(db.Integer, db.ForeignKey('customer.CustomerID'), nullable=False) # Must be linked to a customer
    # --- 已注释掉 PaidDate 字段 ---
    # PaidDate = db.Column(db.DateTime, nullable=True) # Actual payment date
    # ---------------------------
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship (backrefs defined in Sale and Customer)
    # sale = db.relationship('Sale', backref='receivable')
    # customer = db.relationship('Customer', backref='receivables')

    def to_dict(self):
        return {
            'ReceivableID': self.ReceivableID,
            'ReceivableDate': self.ReceivableDate.strftime('%Y-%m-%d') if self.ReceivableDate else None,
            'Status': self.Status,
            'ReceivableAmount': float(self.ReceivableAmount) if self.ReceivableAmount else 0.0,
            'SaleID': self.SaleID,
            'CustomerID': self.CustomerID,
            'customer_name': self.customer.Name if self.customer else 'Unknown',
            # --- 已注释掉 PaidDate 字段的引用 ---
            # 'PaidDate': self.PaidDate.strftime('%Y-%m-%d %H:%M:%S') if self.PaidDate else None,
            # ----------------------------------
            'CreatedAt': self.CreatedAt.strftime('%Y-%m-%d %H:%M:%S') if self.CreatedAt else None # Include CreatedAt
        }


# 送餐平台合作伙伴模型
class DeliveryPlatform(db.Model):
    __tablename__ = 'delivery_platform'
    PlatformID = db.Column(db.Integer, primary_key=True)
    PlatformName = db.Column(db.String(100), nullable=False)
    ContactPerson = db.Column(db.String(50))
    ContactPhone = db.Column(db.String(20))
    Email = db.Column(db.String(100))
    CommissionRate = db.Column(db.Float, nullable=False) # Commission percentage
    SettlementCycle = db.Column(db.String(50)) # e.g., Weekly, Bi-weekly, Monthly
    CooperationStartDate = db.Column(db.Date)
    OrdersThisMonth = db.Column(db.Integer, default=0) # Track recent performance
    Status = db.Column(db.String(20), default='Active') # Active, Inactive, Suspended
    Description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.PlatformID,
            'name': self.PlatformName,
            'contact_person': self.ContactPerson,
            'contact_phone': self.ContactPhone,
            'email': self.Email,
            'commission_rate': self.CommissionRate,
            'settlement_cycle': self.SettlementCycle,
            'cooperation_start_date': self.CooperationStartDate.strftime('%Y-%m-%d') if self.CooperationStartDate else None,
            'orders_this_month': self.OrdersThisMonth,
            'status': self.Status,
            'description': self.Description,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

# 设备维护服务提供商模型
class MaintenanceProvider(db.Model):
    __tablename__ = 'maintenance_provider'
    ProviderID = db.Column(db.Integer, primary_key=True)
    ProviderName = db.Column(db.String(100), nullable=False)
    ServiceType = db.Column(db.String(50)) # e.g., HVAC, Kitchen Equipment, Plumbing
    ContactPerson = db.Column(db.String(50))
    ContactPhone = db.Column(db.String(20))
    Email = db.Column(db.String(100))
    ContractExpiryDate = db.Column(db.Date)
    LastServiceDate = db.Column(db.Date)
    NextServiceDate = db.Column(db.Date)
    MaintenanceCycle = db.Column(db.Integer) # Maintenance cycle in days
    Status = db.Column(db.String(20), default='Active') # Active, Inactive
    Description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.ProviderID,
            'name': self.ProviderName,
            'service_type': self.ServiceType,
            'contact_person': self.ContactPerson,
            'contact_phone': self.ContactPhone,
            'email': self.Email,
            'contract_expiry_date': self.ContractExpiryDate.strftime('%Y-%m-%d') if self.ContractExpiryDate else None,
            'last_service_date': self.LastServiceDate.strftime('%Y-%m-%d') if self.LastServiceDate else None,
            'next_service_date': self.NextServiceDate.strftime('%Y-%m-%d') if self.NextServiceDate else None,
            'maintenance_cycle': self.MaintenanceCycle,
            'status': self.Status,
            'description': self.Description,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }