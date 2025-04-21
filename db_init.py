import random
from datetime import datetime, timedelta, date
from decimal import Decimal # Import Decimal for precise price handling
from models import db, Dish, Item, Inventory, DishIngredient, Vendor, Purchase, PurchaseItem, Sale, SaleDish, Customer, Staff, Feedback, Payable, Receivable # Ensure Receivable is imported

# init_db_data 函数保持不变，但内部的 Receivable 创建逻辑已修改
def init_db_data():
    """Initialize the database and fill with sample data (English)"""

    if Dish.query.count() > 0:
        print("Database already contains data, skipping initialization...")
        return

    print("Starting database initialization...")

    # Clear existing data (ensure correct order for foreign keys)
    PurchaseItem.query.delete()
    SaleDish.query.delete()
    Feedback.query.delete()
    Payable.query.delete()
    Receivable.query.delete()
    Purchase.query.delete()
    Sale.query.delete()
    DishIngredient.query.delete()
    Inventory.query.delete()
    Dish.query.delete()
    Item.query.delete()
    Vendor.query.delete()
    Customer.query.delete()
    Staff.query.delete()
    db.session.commit() # Commit deletions

    # Add Vendors (English)
    vendors = [
        Vendor(
            Name="Summit Food Supply",
            ContactPerson="Mr. Zhang",
            PhoneNum="13912345678",
            Email="summit_foods@example.com",
            Address="123 Summit Road"
        ),
        Vendor(
            Name="Fresh Produce Delivery",
            ContactPerson="Mr. Li",
            PhoneNum="13987654321",
            Email="fresh_produce@example.com",
            Address="456 Produce Ave"
        ),
        Vendor(
            Name="Premium Meat Wholesale",
            ContactPerson="Mr. Wang",
            PhoneNum="13855556666",
            Email="premium_meat@example.com",
            Address="789 Meat St"
        )
    ]
    db.session.add_all(vendors)
    db.session.commit()

    # Add Base Items (English)
    items = [
        Item(Name="High-Gluten Flour", Category="Raw Material", DefaultUnit="kg", Description="Flour for pizza base"),
        Item(Name="Tomato Sauce", Category="Condiment", DefaultUnit="L", Description="Basic pizza sauce"),
        Item(Name="Mozzarella Cheese", Category="Dairy", DefaultUnit="kg", Description="Common pizza cheese"),
        Item(Name="Pepperoni", Category="Meat", DefaultUnit="kg", Description="Classic pizza topping"),
        Item(Name="Mushrooms", Category="Vegetable", DefaultUnit="kg", Description="Fresh mushrooms"),
        Item(Name="Green Peppers", Category="Vegetable", DefaultUnit="kg", Description="Colorful green peppers"),
        Item(Name="Onions", Category="Vegetable", DefaultUnit="kg", Description="Sweet onions"),
        Item(Name="Olive Oil", Category="Oil", DefaultUnit="L", Description="High-quality olive oil"),
        Item(Name="Black Olives", Category="Topping", DefaultUnit="kg", Description="Imported black olives"),
        Item(Name="Italian Seasoning", Category="Condiment", DefaultUnit="kg", Description="Mixed herbs"),
        Item(Name="Ham Slices", Category="Meat", DefaultUnit="kg", Description="Quality ham slices"),
        Item(Name="Pineapple Chunks", Category="Fruit", DefaultUnit="kg", Description="Fresh pineapple chunks"),
        Item(Name="Basil Leaves", Category="Herb", DefaultUnit="kg", Description="Fresh basil leaves")
    ]
    db.session.add_all(items)
    db.session.commit()

    # Add Inventory Records (English)
    inventories = []
    for item in items:
        vendor = random.choice(vendors)
        stock_level = random.randint(20, 150) # Increased initial stock variation
        reorder_level = random.randint(10, 30)
        inventory = Inventory(
            ItemID=item.ItemID,
            StockLevel=stock_level,
            ReorderLevel=reorder_level,
            VendorID=vendor.VendorID,
            last_update=datetime.now() - timedelta(days=random.randint(1, 5)) # Slightly varied last update
        )
        inventories.append(inventory)
    db.session.add_all(inventories)
    db.session.commit()

    # Add Dishes (English, Lower Prices)
    dishes = [
        Dish(
            Name="Classic Margherita Pizza",
            Price=Decimal('12.99'), # Lower price
            Category="Pizza",
            Description="Classic Italian pizza with tomato sauce, mozzarella, and basil",
            Status="Available",
            ImageURL="/static/img/pizza1.jpg"
        ),
        Dish(
            Name="Spicy Pepperoni Pizza",
            Price=Decimal('14.99'), # Lower price
            discount_price=Decimal('13.99'), # Lower discount price
            Category="Pizza",
            Description="Spicy pepperoni with mozzarella cheese and fresh chili",
            Status="Available",
            ImageURL="/static/img/pizza2.jpg"
        ),
        Dish(
            Name="Mushroom & Cheese Pizza",
            Price=Decimal('11.99'), # Lower price
            Category="Pizza",
            Description="Delicious mushrooms combined with rich cheese",
            Status="Available",
            ImageURL="/static/img/pizza3.jpg"
        ),
        Dish(
            Name="Hawaiian Pizza",
            Price=Decimal('13.49'), # Lower price
            Category="Pizza",
            Description="Classic combination of ham and pineapple",
            Status="Available",
            ImageURL="/static/img/pizza4.jpg"
        ),
        Dish(
            Name="Garlic Bread Sticks",
            Price=Decimal('5.99'), # Lower price
            Category="Sides",
            Description="Crispy and delicious garlic bread sticks",
            Status="Available",
            ImageURL="/static/img/sides1.jpg"
        ),
        Dish(
            Name="Italian Salad",
            Price=Decimal('7.99'), # Lower price
            Category="Salad",
            Description="Fresh vegetables with special salad dressing",
            Status="Available",
            ImageURL="/static/img/salad1.jpg"
        ),
        Dish(
            Name="Cola",
            Price=Decimal('2.49'), # Lower price
            Category="Drinks",
            Description="Classic Coca-Cola",
            Status="Available",
            ImageURL="/static/img/drink1.jpg"
        ),
        Dish(
            Name="Iced Tea",
            Price=Decimal('2.49'), # Lower price
            Category="Drinks",
            Description="Homemade iced tea",
            Status="Available",
            ImageURL="/static/img/drink2.jpg"
        )
    ]
    db.session.add_all(dishes)
    db.session.commit()

    # Add Dish Ingredients (assuming IDs are stable after commit)
    dish_ingredients = []
    # Classic Margherita Pizza ingredients
    dish_ingredients.extend([
        DishIngredient(DishID=dishes[0].DishID, ItemID=items[0].ItemID, Quantity=0.25), # Flour
        DishIngredient(DishID=dishes[0].DishID, ItemID=items[1].ItemID, Quantity=0.10), # Tomato Sauce
        DishIngredient(DishID=dishes[0].DishID, ItemID=items[2].ItemID, Quantity=0.15), # Mozzarella
        DishIngredient(DishID=dishes[0].DishID, ItemID=items[7].ItemID, Quantity=0.02), # Olive Oil
        DishIngredient(DishID=dishes[0].DishID, ItemID=items[12].ItemID, Quantity=0.03), # Basil Leaves
    ])
    # Spicy Pepperoni Pizza ingredients
    dish_ingredients.extend([
        DishIngredient(DishID=dishes[1].DishID, ItemID=items[0].ItemID, Quantity=0.25), # Flour
        DishIngredient(DishID=dishes[1].DishID, ItemID=items[1].ItemID, Quantity=0.10), # Tomato Sauce
        DishIngredient(DishID=dishes[1].DishID, ItemID=items[2].ItemID, Quantity=0.15), # Mozzarella
        DishIngredient(DishID=dishes[1].DishID, ItemID=items[3].ItemID, Quantity=0.10), # Pepperoni
        DishIngredient(DishID=dishes[1].DishID, ItemID=items[5].ItemID, Quantity=0.05), # Green Peppers
    ])
    # Mushroom & Cheese Pizza ingredients
    dish_ingredients.extend([
        DishIngredient(DishID=dishes[2].DishID, ItemID=items[0].ItemID, Quantity=0.25), # Flour
        DishIngredient(DishID=dishes[2].DishID, ItemID=items[1].ItemID, Quantity=0.10), # Tomato Sauce
        DishIngredient(DishID=dishes[2].DishID, ItemID=items[2].ItemID, Quantity=0.18), # Mozzarella
        DishIngredient(DishID=dishes[2].DishID, ItemID=items[4].ItemID, Quantity=0.12), # Mushrooms
    ])
    # Hawaiian Pizza ingredients
    dish_ingredients.extend([
        DishIngredient(DishID=dishes[3].DishID, ItemID=items[0].ItemID, Quantity=0.25), # Flour
        DishIngredient(DishID=dishes[3].DishID, ItemID=items[1].ItemID, Quantity=0.10), # Tomato Sauce
        DishIngredient(DishID=dishes[3].DishID, ItemID=items[2].ItemID, Quantity=0.15), # Mozzarella
        DishIngredient(DishID=dishes[3].DishID, ItemID=items[10].ItemID, Quantity=0.08), # Ham
        DishIngredient(DishID=dishes[3].DishID, ItemID=items[11].ItemID, Quantity=0.08), # Pineapple
    ])
    # Garlic Bread Sticks ingredients
    dish_ingredients.extend([
        DishIngredient(DishID=dishes[4].DishID, ItemID=items[0].ItemID, Quantity=0.15), # Flour
        DishIngredient(DishID=dishes[4].DishID, ItemID=items[7].ItemID, Quantity=0.04), # Olive Oil
    ])
    # Salad & Drinks don't need ingredients listed here for stock mgmt demo
    db.session.add_all(dish_ingredients)
    db.session.commit()

    # —— 6. 员工（Staff）
    staffs = [
        Staff(
            staff_code="ST001",
            name="Manager Chen",
            position="Manager",
            department="Management",
            email="chen_manager@example.com",
            phone="13812345678",
            join_date=datetime.now() - timedelta(days=400),
            status="Active",
            address="Staff Dorm A101",
            performance=random.randint(80, 150)
        ),
        Staff(
            staff_code="ST002",
            name="Chef Li",
            position="Head Chef",
            department="Kitchen",
            email="li_chef@example.com",
            phone="13823456789",
            join_date=datetime.now() - timedelta(days=200),
            status="Active",
            address="Staff Dorm A102",
            performance=random.randint(80, 150)
        ),
        Staff(
            staff_code="ST003",
            name="Waiter Wang",
            position="Waiter",
            department="Service",
            email="wang_waiter@example.com",
            phone="13834567890",
            join_date=datetime.now() - timedelta(days=100),
            status="Active",
            address="Staff Dorm B101",
            performance=random.randint(80, 150)
        ),
        Staff(
            staff_code="ST004",
            name="Cashier Zhao",
            position="Cashier",
            department="Front Desk",
            email="zhao_cashier@example.com",
            phone="13845678901",
            join_date=datetime.now() - timedelta(days=50),
            status="On Leave",
            address="Staff Dorm B102",
            performance=random.randint(80, 150)
        ),
    ]
    db.session.add_all(staffs)
    db.session.commit()

    # Add Customers (English, Increased Count: 20)
    # —— 固定 20 位顾客数据（部分 ≥60 岁，部分 <60 岁） —— #
    customers = []
    data = [
        # 60 岁以上
        {"name":"Alice Smith",     "birth":date(1950,  5, 14), "mem":"Gold"},
        {"name":"Bob Johnson",     "birth":date(1955, 11,  2), "mem":"Silver"},
        {"name":"Charlie Williams","birth":date(1948,  7, 30), "mem":"Bronze"},
        {"name":"David Brown",     "birth":date(1962,  9, 10), "mem":"Regular"},
        {"name":"Eve Jones",       "birth":date(1958,  3, 22), "mem":"Gold"},

        # 60 岁以下
        {"name":"Frank Garcia",    "birth":date(1985, 12,  1), "mem":"Silver"},
        {"name":"Grace Miller",    "birth":date(1990,  6, 18), "mem":"Bronze"},
        {"name":"Heidi Davis",     "birth":date(1975,  4, 25), "mem":"Regular"},
        {"name":"Ivan Rodriguez",  "birth":date(2000,  2, 14), "mem":"Gold"},
        {"name":"Judy Martinez",   "birth":date(1995, 10,  9), "mem":"Silver"},

        # 再补 10 位混合
        {"name":"Kevin Wilson",    "birth":date(1961,  1,  5), "mem":"Bronze"},  # 60+
        {"name":"Linda Moore",     "birth":date(1970,  8, 12), "mem":"Regular"},
        {"name":"Mike Taylor",     "birth":date(1959, 11, 20), "mem":"Gold"},   # 60+
        {"name":"Nancy Anderson",  "birth":date(1988,  7,  3), "mem":"Silver"},
        {"name":"Oscar Thomas",    "birth":date(1992,  9, 29), "mem":"Bronze"},
        {"name":"Pamela Lee",      "birth":date(1957,  5, 17), "mem":"Regular"},# 60+
        {"name":"Quentin Harris",  "birth":date(1982,  3,  8), "mem":"Gold"},
        {"name":"Rachel Clark",    "birth":date(1999, 12, 26), "mem":"Silver"},
        {"name":"Steve Lewis",     "birth":date(1964,  2, 11), "mem":"Bronze"},  # 60+
        {"name":"Tracy Walker",    "birth":date(1978, 10, 15), "mem":"Regular"},
    ]

    for idx, info in enumerate(data, start=1):
        # 注册和最后访问时间，可以根据需求自由调整
        reg_date   = datetime.now() - timedelta(days=30 + idx * 2)
        last_visit = datetime.now() - timedelta(days=idx)
        email = f"user{idx}@example.com"
        phone = f"137{10000000 + idx:08d}"

        cust = Customer(
            Name      = info["name"],
            PhoneNum  = phone,
            Email     = email,
            MemLevel  = info["mem"],
            RegDate   = reg_date,
            BirthDate = info["birth"],
            last_visit= last_visit
        )
        customers.append(cust)

    db.session.add_all(customers)
    db.session.commit()

    # Add Sales Records (English Status/Channel, Improved Logic)
    sales = []
    sale_dishes = []
    today = datetime.now()
    num_sales = 250 # Increased number of sales

    channels = ["Dine-in", "Takeaway", "App Order", "Web Order"]
    statuses = ["Completed", "Pending", "Cancelled", "Delivered"]
    status_weights = [0.7, 0.1, 0.05, 0.15] # Completed, Pending, Cancelled, Delivered
    channel_weights = [0.5, 0.25, 0.15, 0.10] # Dine-in, Takeaway, App, Web

    for i in range(num_sales):
        customer = random.choice(customers)
        channel = random.choices(channels, weights=channel_weights, k=1)[0]
        status = random.choices(statuses, weights=status_weights, k=1)[0]

        days_ago = max(0, int(random.gauss(15, 20)))
        if days_ago > 90: days_ago = random.randint(60, 90)

        hour = int(random.gauss(18, 4))
        if hour < 9: hour = random.randint(9, 12)
        if hour > 22: hour = random.randint(20, 22)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        random_sale_date = today - timedelta(days=days_ago, hours=(today.hour - hour), minutes=(today.minute-minute), seconds=(today.second-second))

        if channel == "Dine-in":
            order_type = "Dine-in"
        elif channel == "Takeaway":
            order_type = "Pickup"
        elif channel in ["App Order", "Web Order"]:
            order_type = random.choice(["Delivery", "Pickup"])
        else:
            order_type = "Unknown"

        total_amount = 0.0
        temp_sale_dishes = []
        num_dishes_in_sale = random.randint(1, 5)
        k_dishes = min(len(dishes), num_dishes_in_sale)
        selected_dishes = random.sample(dishes, k=k_dishes)

        for dish in selected_dishes:
            quantity = random.choices([1, 2], weights=[0.85, 0.15], k=1)[0]
            price_to_use = float(dish.discount_price) if dish.discount_price else float(dish.Price)
            total_amount += price_to_use * float(quantity)
            # Store Decimal price for SaleDish creation if needed, but keep calculation float
            temp_sale_dishes.append({'DishID': dish.DishID, 'Quantity': quantity, 'Price': Decimal(str(price_to_use))})

        discount_amount = 0.0
        if status == "Completed" or status == "Delivered":
            if customer.MemLevel == "Gold":
                discount_amount = total_amount * 0.1
            elif customer.MemLevel == "Silver":
                discount_amount = total_amount * 0.05
            elif customer.MemLevel == "Bronze":
                discount_amount = total_amount * 0.02

        if status == "Cancelled":
            discount_amount = 0.0

        final_total_amount = total_amount - discount_amount

        # Determine payment status
        if status in ["Completed", "Delivered"]:
            is_paid = random.random() < 0.9 # 90% chance paid
        else:
            is_paid = False # Pending or Cancelled orders are not paid

        sale = Sale(
            CustomerID=customer.CustomerID,
            SaleDate=random_sale_date,
            TotalAmount=round(final_total_amount, 2),
            DiscountAmount=round(discount_amount, 2),
            Status=status,
            Channel=channel,
            OrderType=order_type,
            PaymentCompleted=is_paid # Assign the calculated payment status
        )
        sales.append(sale)
        # Temporarily store dish info for SaleDish creation after Sale gets ID
        sale._temp_sale_dishes = [{'DishID': d['DishID'], 'Quantity': d['Quantity'], 'Price': d['Price']} for d in temp_sale_dishes]

    db.session.add_all(sales)
    db.session.commit() # Commit Sales to get SaleIDs

    # Create SaleDish records
    for sale in sales:
        if hasattr(sale, '_temp_sale_dishes') and sale._temp_sale_dishes:
            for temp_dish in sale._temp_sale_dishes:
                sale_dish = SaleDish(
                    SaleID=sale.SaleID,
                    DishID=temp_dish['DishID'],
                    Quantity=temp_dish['Quantity'],
                    UnitPrice=float(temp_dish['Price'].quantize(Decimal('0.01'))) # Use stored Decimal, convert to float
                )
                sale_dishes.append(sale_dish)
            del sale._temp_sale_dishes
        else:
             print(f"Warning: SaleID {sale.SaleID} has no temporary dish data to process.")

    db.session.add_all(sale_dishes)
    db.session.commit()

    # Add Sample Payables (Optional, if needed)
    # You might want to generate these based on Purchase records if you have them
    # For now, keeping the simple hardcoded example for payables
    payables = [
        Payable(VendorID=vendors[0].VendorID, PayableAmount=1500.50, PayableDate=datetime.now() + timedelta(days=15), PayableStatus='Unpaid'),
        Payable(VendorID=vendors[1].VendorID, PayableAmount=850.00, PayableDate=datetime.now() - timedelta(days=5), PayableStatus='Unpaid'), # Overdue
        Payable(VendorID=vendors[0].VendorID, PayableAmount=1200.00, PayableDate=datetime.now() - timedelta(days=35), PayableStatus='Paid')
    ]
    db.session.add_all(payables)
    # Removed commit here to commit receivables and payables together

    # Generate Receivables from unpaid Sales (NEW LOGIC)
    print("Generating Receivables from unpaid Sales...")
    receivables_to_add = []
    unpaid_sales = Sale.query.filter_by(PaymentCompleted=False).all()
    print(f"Found {len(unpaid_sales)} unpaid sales to create receivables for.")

    for sale in unpaid_sales:
        if isinstance(sale.SaleDate, datetime):
            receivable_date = sale.SaleDate + timedelta(days=14)
            new_receivable = Receivable(
                ReceivableDate=receivable_date,
                Status='Unpaid',
                ReceivableAmount=sale.TotalAmount, # Use Sale's final total amount
                SaleID=sale.SaleID,
                CustomerID=sale.CustomerID
            )
            receivables_to_add.append(new_receivable)
        else:
             print(f"Warning: SaleID {sale.SaleID} has an invalid SaleDate type ({type(sale.SaleDate)}), skipping receivable creation.")


    if receivables_to_add:
        db.session.add_all(receivables_to_add)
        print(f"Adding {len(receivables_to_add)} new Receivable records to the session.")

    # Commit both Payables and newly generated Receivables
    db.session.commit()
    print("Committed Payables and Receivables.")

    # Add Sample Feedback (English)
    feedbacks = []
    # Ensure we sample from sales that have CustomerID and are Completed
    eligible_sales_for_feedback = [s for s in sales if s.CustomerID and s.Status == 'Completed']
    sample_size = min(15, len(eligible_sales_for_feedback)) # Sample at most 15 or the number of eligible sales

    for sale in random.sample(eligible_sales_for_feedback, sample_size):
         feedback = Feedback(
             Rating=random.randint(3, 5),
             Comment=random.choice([
                 "Great pizza, great service!",
                 "Food was good, but delivery was a bit slow.",
                 "Very satisfied, will come again!",
                 "Reasonable price, excellent quality.",
                 "Nice ambiance, delicious food.",
                 "Could be better, toppings were sparse.",
                 "My favorite pizza place!",
                 "Staff was friendly and helpful."
             ]),
             CreateTime=sale.SaleDate + timedelta(hours=random.randint(1, 48)),
             CustomerID=sale.CustomerID,
             SaleID=sale.SaleID
         )
         feedbacks.append(feedback)
    if feedbacks: # Only add if feedbacks were generated
        db.session.add_all(feedbacks)
        db.session.commit()

    print("Data initialization complete!")
def init_db():
    """Create database tables and initialize data (English)"""
    db.drop_all() # Force drop existing tables
    db.create_all()
    print("Database tables created!")
    # Optionally: Automatically populate data after creating tables
    init_db_data()
    # return "Database initialization successful!" # Return was causing issues with flask cli call