# blueprints/order_bp.py

from flask import Blueprint, render_template, request, jsonify, current_app
from sqlalchemy.orm import joinedload
from sqlalchemy import func, desc
# 确保导入 timedelta 和 Receivable 模型, datetime
from datetime import date, datetime, timedelta
from decimal import Decimal
from models import db, Sale, Customer, SaleDish, Dish, Receivable # <--- 导入 Receivable

# Blueprint for rendering order management pages
order_bp = Blueprint('order_bp', __name__, template_folder='../templates')

# Blueprint for order-related API endpoints
order_api = Blueprint('order_api', __name__, url_prefix='/api/orders')

@order_bp.route('/management')
def orders_management():
    """Renders the order management page."""
    return render_template('orders/orders_management.html', title="Order Management")

@order_api.route('/all', methods=['GET'])
def get_sales():
    """API endpoint to get sales data with filtering and pagination."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 15, type=int) # Default to 15 as per template
        sort_by = request.args.get('sort_by', 'SaleDate')
        sort_order = request.args.get('sort_order', 'desc')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        status_filter = request.args.get('status')
        channel_filter = request.args.get('channel')
        # --- 新增支付状态过滤 ---
        payment_completed_str = request.args.get('payment_completed') 
        payment_completed_filter = None
        if payment_completed_str is not None:
             payment_completed_filter = payment_completed_str.lower() == 'true'
        # -----------------------


        # Base query joining Sale and Customer (only select SaleID initially for filtering)
        base_query = db.session.query(Sale.SaleID) \
            .join(Customer, Sale.CustomerID == Customer.CustomerID, isouter=True) # Use outer join for guest orders

        # Apply filters
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            base_query = base_query.filter(Sale.SaleDate >= start_date)
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
            base_query = base_query.filter(Sale.SaleDate < end_date)
        if status_filter:
            base_query = base_query.filter(Sale.Status == status_filter)
        if channel_filter:
            base_query = base_query.filter(Sale.Channel == channel_filter)
        # --- 应用支付状态过滤 ---
        if payment_completed_filter is not None:
            base_query = base_query.filter(Sale.PaymentCompleted == payment_completed_filter)
        # -----------------------


        # Get total count before pagination for correct total_items
        total_items = base_query.count()

        # Apply sorting *before* pagination on the SaleID query
        sort_column_base = Sale.SaleDate # Default
        if sort_by == 'CustomerName':
             # Sorting by CustomerName requires joining Customer earlier if needed
             # This approach might be less performant. Consider if sorting by CustomerName is critical.
             # If so, might need to adjust the query structure.
             # For now, we default to SaleDate if CustomerName is requested for simplicity
             # sort_column_base = Customer.Name
             pass
        elif hasattr(Sale, sort_by):
            sort_column_base = getattr(Sale, sort_by)

        if sort_order.lower() == 'asc':
            base_query = base_query.order_by(sort_column_base.asc())
        else:
            base_query = base_query.order_by(sort_column_base.desc())


        # Apply pagination to the SaleID query
        paginated_ids_query = base_query.paginate(page=page, per_page=per_page, error_out=False)
        sale_ids_on_page = [item.SaleID for item in paginated_ids_query.items]

        if not sale_ids_on_page:
            # No results for this page
            return jsonify({
                'sales': [],
                'total_items': total_items,
                'current_page': page,
                'total_pages': paginated_ids_query.pages,
                'per_page': per_page
            })


        # Main query to fetch details only for the SaleIDs on the current page
        main_query = db.session.query(
            Sale.SaleID,
            Sale.SaleDate,
            Customer.Name.label('CustomerName'),
            Sale.TotalAmount,
            Sale.Status,
            Sale.Channel,
            Sale.OrderType,
            Sale.DiscountAmount,
            Sale.PaymentCompleted, # Fetch the PaymentCompleted status
            # Use coalesce for sum to handle cases with no dishes
            func.coalesce(db.func.sum(SaleDish.Quantity), 0).label('TotalQuantity'),
            # group_concat without inner ORDER BY for broader compatibility
            db.func.group_concat(Dish.Name).label('Dishes')
        ).select_from(Sale) \
         .filter(Sale.SaleID.in_(sale_ids_on_page)) \
         .outerjoin(Customer, Sale.CustomerID == Customer.CustomerID) \
         .outerjoin(SaleDish, Sale.SaleID == SaleDish.SaleID) \
         .outerjoin(Dish, SaleDish.DishID == Dish.DishID) \
         .group_by(
            Sale.SaleID,
            Sale.SaleDate,
            Customer.Name,
            Sale.TotalAmount,
            Sale.Status,
            Sale.Channel,
            Sale.OrderType,
            Sale.DiscountAmount,
            Sale.PaymentCompleted # Group by PaymentCompleted as well
         )

        # Re-apply the same sorting order to the final results
        sort_column_final = Sale.SaleDate # Default
        if sort_by == 'CustomerName':
             # sort_column_final = Customer.Name # Requires Customer join
             pass # Defaulting to SaleDate
        elif hasattr(Sale, sort_by):
            sort_column_final = getattr(Sale, sort_by)

        if sort_order.lower() == 'asc':
            main_query = main_query.order_by(sort_column_final.asc())
        else:
            main_query = main_query.order_by(sort_column_final.desc())


        sales_data = main_query.all()

        # Convert results to dictionary
        sales_list = []
        for sale in sales_data:
            dishes_str = sale.Dishes
            # Sort dishes alphabetically if needed after fetching
            dish_list_sorted = sorted(dishes_str.split(',')) if dishes_str else []
            sales_list.append({
                'SaleID': sale.SaleID,
                'SaleDate': sale.SaleDate.strftime('%Y-%m-%d %H:%M:%S'),
                'CustomerName': sale.CustomerName or 'Guest', # Handle guest orders
                'TotalAmount': float(sale.TotalAmount or 0.0),
                'DiscountAmount': float(sale.DiscountAmount or 0.0),
                'Status': sale.Status,
                'Channel': sale.Channel,
                'OrderType': sale.OrderType,
                'PaymentCompleted': sale.PaymentCompleted, # Include in response
                'Dishes': ', '.join(dish_list_sorted) if dish_list_sorted else 'N/A',
                'TotalQuantity': int(sale.TotalQuantity) # Already coalesced to 0
            })

        # Ensure the order matches the paginated IDs order if necessary
        # (Usually SQLAlchemy handles this if the order by is consistent)

        return jsonify({
            'sales': sales_list,
            'total_items': total_items,
            'current_page': page,
            'total_pages': paginated_ids_query.pages,
            'per_page': per_page
        })

    except Exception as e:
        current_app.logger.error(f"Error fetching sales data: {e}", exc_info=True) # Log full traceback
        return jsonify({'error': 'Failed to retrieve sales data', 'message': str(e)}), 500

# Get details for a specific order
@order_api.route('/<int:sale_id>', methods=['GET'])
def get_order_details(sale_id):
    """API endpoint to get details for a specific sale/order."""
    try:
        # Use joinedload to efficiently fetch related customer and items/dishes
        sale = db.session.query(Sale).options(
            joinedload(Sale.customer),
            joinedload(Sale.items).joinedload(SaleDish.dish) # Load Sale -> SaleDish -> Dish
        ).get(sale_id)

        if not sale:
            return jsonify({"error": "Order not found"}), 404

        sale_details = {
            'SaleID': sale.SaleID,
            'SaleDate': sale.SaleDate.strftime('%Y-%m-%d %H:%M:%S') if sale.SaleDate else None,
            'CustomerName': sale.customer.Name if sale.customer else 'Guest', # Handle Guest
            'CustomerID': sale.CustomerID,
            'TotalAmount': float(sale.TotalAmount) if sale.TotalAmount else 0.0,
            'DiscountAmount': float(sale.DiscountAmount) if sale.DiscountAmount else 0.0,
            'FinalAmount': float(sale.TotalAmount - (sale.DiscountAmount or Decimal(0))) if sale.TotalAmount else 0.0, # Use Decimal for calc
            'Status': sale.Status,
            'Channel': sale.Channel,
            'OrderType': sale.OrderType,
            'PaymentCompleted': sale.PaymentCompleted, # Include payment status
            'Dishes': [
                {
                    'DishName': item.dish.Name if item.dish else 'Unknown',
                    'Quantity': item.Quantity,
                    'UnitPrice': float(item.UnitPrice) if item.UnitPrice else 0.0
                } for item in sale.items # Iterate through loaded items
            ]
        }
        return jsonify(sale_details)

    except Exception as e:
        current_app.logger.error(f"Error fetching order details for ID {sale_id}: {e}", exc_info=True)
        return jsonify({"error": "Could not fetch order details", "details": str(e)}), 500


# Create a new order
@order_api.route('/create', methods=['POST'])
def create_order():
    """API endpoint to create a new sale and conditionally a receivable."""
    data = request.get_json()
    current_app.logger.info(f"Received create order request: {data}")

    if not data or 'items' not in data or not data['items']:
        current_app.logger.error("Missing required sales data or item details")
        return jsonify({'error': 'Missing required sales data or item details.'}), 400

    # Use a try-except block for the whole process
    try:
        customer_id = data.get('customer_id') # Optional
        order_type = data.get('order_type', 'Unknown')
        channel = data.get('channel', 'Unknown')
        sale_items_data = data.get('items', [])
        # Get payment status, default to False (unpaid) if not provided
        payment_completed = data.get('payment_completed', False)
        discount_input = data.get('discount_amount', 0)

        # Validate discount amount
        try:
            discount_decimal = Decimal(str(discount_input)) # Use Decimal
        except (ValueError, TypeError):
            current_app.logger.error(f"Invalid discount amount received: {discount_input}")
            return jsonify({'error': 'Invalid discount amount format.'}), 400

        current_app.logger.info(f"Processing order: CustomerID={customer_id}, Type={order_type}, Channel={channel}, Items={len(sale_items_data)}, PaymentCompleted={payment_completed}, Discount={discount_decimal}")

        if not order_type or not channel:
             current_app.logger.error("Order type and channel are required")
             return jsonify({'error': 'Order type and channel are required.'}), 400

        total_amount_decimal = Decimal(0) # Use Decimal for calculations
        sale_items_to_create = []

        # Process items
        for i, item_data in enumerate(sale_items_data):
            dish_id = item_data.get('dish_id')
            quantity = item_data.get('quantity')
            current_app.logger.info(f"Processing item #{i+1}: dish_id={dish_id}, quantity={quantity}")

            if not dish_id or quantity is None or not isinstance(quantity, int) or quantity <= 0:
                 current_app.logger.error(f"Invalid item data: {item_data}. Dish ID and positive integer quantity required")
                 return jsonify({'error': f'Invalid item data for item {i+1}. Dish ID and positive integer quantity required.'}), 400


            dish = Dish.query.get(dish_id)
            if not dish:
                current_app.logger.error(f"Dish with ID {dish_id} not found")
                return jsonify({'error': f'Dish with ID {dish_id} not found.'}), 404

            # Determine unit price (use discount price if available) - Use Decimal
            unit_price_decimal = dish.discount_price if dish.discount_price is not None else dish.Price
            if unit_price_decimal is None:
                current_app.logger.error(f"Dish {dish_id} ('{dish.Name}') has no price defined.")
                return jsonify({'error': f"Price not defined for dish '{dish.Name}'."}), 400

            subtotal_decimal = unit_price_decimal * Decimal(quantity)
            total_amount_decimal += subtotal_decimal

            current_app.logger.info(f"Item #{i+1}: Dish='{dish.Name}', UnitPrice={unit_price_decimal}, Quantity={quantity}, Subtotal={subtotal_decimal}")

            sale_items_to_create.append({
                'dish_id': dish_id,
                'quantity': quantity,
                'unit_price': unit_price_decimal,
                'subtotal': subtotal_decimal
            })

        # Calculate final total after discount
        final_total_decimal = total_amount_decimal - discount_decimal
        final_total_decimal = max(Decimal(0), final_total_decimal) # Ensure total is not negative

        # Create Sale record
        sale_date_to_use = datetime.utcnow() # Use a consistent timestamp
        new_sale = Sale(
            CustomerID=customer_id if customer_id else None, # Allow None for guests
            SaleDate=sale_date_to_use,
            TotalAmount=final_total_decimal, # Store as Decimal
            DiscountAmount=discount_decimal, # Store as Decimal
            Status='Pending', # New orders start as Pending
            OrderType=order_type,
            Channel=channel,
            PaymentCompleted=payment_completed # Save the payment status from request
        )
        db.session.add(new_sale)
        current_app.logger.info(f"Sale record created, preparing to flush to get SaleID")
        # Flush to get the SaleID before creating SaleDish and Receivable
        db.session.flush()
        current_app.logger.info(f"Obtained new SaleID: {new_sale.SaleID}")

        # Create SaleDish records
        for i, item in enumerate(sale_items_to_create):
            sale_dish_record = SaleDish(
                SaleID=new_sale.SaleID,
                DishID=item['dish_id'],
                Quantity=item['quantity'],
                UnitPrice=item['unit_price'], # Store as Decimal
            )
            db.session.add(sale_dish_record)
            current_app.logger.info(f"SaleDish record #{i+1} added: SaleID={new_sale.SaleID}, DishID={item['dish_id']}, Quantity={item['quantity']}")

        # Conditionally create Receivable IF PaymentCompleted is False
        if not payment_completed:
            # Only create receivable if there's a customer associated
            if new_sale.CustomerID:
                receivable_date = sale_date_to_use.date() + timedelta(days=14) # Use date part + timedelta
                new_receivable = Receivable(
                    ReceivableDate=receivable_date,
                    Status='Unpaid',
                    ReceivableAmount=new_sale.TotalAmount, # Use the final calculated amount (Decimal)
                    SaleID=new_sale.SaleID,
                    CustomerID=new_sale.CustomerID,
                    CreatedAt=datetime.utcnow() # Add creation timestamp
                    # PaidDate is not included here anymore
                )
                db.session.add(new_receivable)
                current_app.logger.info(f"Created Receivable record for SaleID {new_sale.SaleID}, Amount: {new_sale.TotalAmount}")
            else:
                 # Log if no customer ID is present for an unpaid sale
                 current_app.logger.warning(f"SaleID {new_sale.SaleID} is unpaid but has no CustomerID. Receivable not created.")
        else:
            current_app.logger.info(f"SaleID {new_sale.SaleID} is marked as paid. No Receivable created.")


        # Commit everything (Sale, SaleDishes, and potentially Receivable)
        db.session.commit()
        current_app.logger.info(f"Order creation committed successfully to database, SaleID={new_sale.SaleID}")

        # Fetch customer name for response if needed (already handled in Sale.to_dict)
        # customer_name = new_sale.customer.Name if new_sale.customer else 'Guest'

        # Prepare response data using the model's to_dict method
        created_sale_data = new_sale.to_dict()

        current_app.logger.info(f"Returning created sale details: SaleID={new_sale.SaleID}")
        return jsonify({'message': 'Order created successfully.', 'sale': created_sale_data}), 201

    except Exception as e:
        db.session.rollback() # Rollback on any error
        current_app.logger.error(f"Error during order creation: {e}", exc_info=True)
        error_type = type(e).__name__
        return jsonify({'error': f'An error occurred during order creation.', 'details': str(e), 'type': error_type}), 500


# Update order status
@order_api.route('/<int:sale_id>/status', methods=['PUT'])
def update_order_status(sale_id):
    """API endpoint to update the status of a specific sale."""
    data = request.get_json()
    new_status = data.get('status')

    if not new_status:
        return jsonify({'error': 'New status is required.'}), 400

    allowed_statuses = ['Pending', 'Processing', 'Delivered', 'Completed', 'Cancelled']
    if new_status not in allowed_statuses:
         return jsonify({'error': f'Invalid status value. Allowed statuses: {", ".join(allowed_statuses)}'}), 400

    try:
        sale = Sale.query.get_or_404(sale_id)
        old_status = sale.Status # Store old status if needed for logic below

        sale.Status = new_status
        # sale.LastUpdated = datetime.utcnow() # Optional: Track update time

        # --- Logic for linked Receivable ---
        # If order is Cancelled, update associated Receivable to 'Cancelled' (if unpaid)
        if new_status == 'Cancelled':
             receivable = Receivable.query.filter_by(SaleID=sale_id).first()
             if receivable and receivable.Status == 'Unpaid':
                 receivable.Status = 'Cancelled' # Assuming Receivable model has this status
                 current_app.logger.info(f"Sale {sale_id} cancelled, updating associated Receivable {receivable.ReceivableID} status to Cancelled.")

        # Note: Marking sale 'Completed' does NOT automatically mark it as paid here.
        # Use the '/mark_paid' endpoint for that.

        db.session.commit()

        return jsonify({'success': True, 'message': f'Sale #{sale_id} status updated to {new_status}.', 'new_status': new_status})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating status for sale ID {sale_id}: {e}", exc_info=True)
        return jsonify({'error': 'An error occurred while updating the sale status.'}), 500


# --- MODIFIED ENDPOINT TO MARK AS PAID ---
@order_api.route('/<int:sale_id>/mark_paid', methods=['PUT'])
def mark_order_paid(sale_id):
    """API endpoint to mark a specific sale as paid."""
    current_app.logger.info(f"Received request to mark order {sale_id} as paid")
    try:
        sale = Sale.query.get(sale_id)
        if not sale:
            current_app.logger.warning(f"Order {sale_id} not found")
            return jsonify({'error': 'Order not found'}), 404

        if sale.PaymentCompleted:
            current_app.logger.info(f"Order {sale_id} is already marked as paid")
            # Return success even if already paid, as the state is correct
            return jsonify({'message': 'Order is already marked as paid', 'sale': sale.to_dict()}), 200

        # 1. Update Sale record
        sale.PaymentCompleted = True
        # Optional: Update status if needed based on business logic
        # Example: if sale.Status == 'Delivered': sale.Status = 'Completed'

        # 2. Find and update associated Receivable record
        #    This query should now work because PaidDate is removed from the model
        receivable = Receivable.query.filter_by(SaleID=sale_id).first()
        if receivable:
            if receivable.Status != 'Paid':
                receivable.Status = 'Paid'
                # --- PaidDate assignment removed ---
                # receivable.PaidDate = datetime.utcnow() # Record payment time
                current_app.logger.info(f"Associated Receivable {receivable.ReceivableID} updated to Paid")
            else:
                 current_app.logger.info(f"Associated Receivable {receivable.ReceivableID} was already Paid")
        else:
             # This might happen if the order was paid upfront (PaymentCompleted=True initially)
             # Or if it was a guest order without a CustomerID (Receivable wasn't created)
             current_app.logger.info(f"No unpaid Receivable record found for paid order {sale_id}.")

        # 3. Commit database changes
        db.session.commit()
        current_app.logger.info(f"Order {sale_id} successfully marked as paid and associated records updated")

        # Return updated sale details
        return jsonify({'success': True, 'message': f'Sale #{sale_id} marked as paid.', 'sale': sale.to_dict()})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error marking order {sale_id} as paid: {e}", exc_info=True)
        # The error should no longer be "no such column: receivable.PaidDate"
        return jsonify({'error': 'An error occurred while marking the order as paid.', 'details': str(e)}), 500
# --- END OF MODIFIED ENDPOINT ---