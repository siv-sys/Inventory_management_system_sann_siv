import os
import random
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

# ------------------------------------------------------------------------------
# Flask App Configuration
# ------------------------------------------------------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'inventory-system-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory_new.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ------------------------------------------------------------------------------
# Models
# ------------------------------------------------------------------------------

class User(db.Model):
    __tablename__ = 'users'
   
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    image_url = db.Column(db.String(200), default=None)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Product(db.Model):
    __tablename__ = 'products'
   
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    
    product = db.relationship('Product', backref='order_items')


class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(20), unique=True, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(100))
    customer_phone = db.Column(db.String(20))
    order_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pending')
    tracking_number = db.Column(db.String(50))
    shipping_address = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    items = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan')


class Sale(db.Model):
    __tablename__ = 'sales'
   
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity_sold = db.Column(db.Integer, nullable=False)
    sale_price = db.Column(db.Float, nullable=False)
    sale_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    product = db.relationship('Product', backref='sales')


# ------------------------------------------------------------------------------
# Database Initialization
# ------------------------------------------------------------------------------


def init_database():
    """Initialize the database with sample data"""
    with app.app_context():
        # Drop all tables and recreate them to ensure schema matches models
        print("🔄 Recreating database tables...")
        db.drop_all()
        db.create_all()
        print("✅ Created new database with all tables")
        
        # Create default user
        print("📝 Creating default user...")
        default_user = User(
            name='Demo User',
            email='demo@example.com',
            image_url=None
        )
        default_user.set_password('password123')
        db.session.add(default_user)
        db.session.commit()
        
        # Create sample products
        print("📦 Creating sample products...")
        sample_products = [
            Product(name='MacBook Pro 16"', category='Electronics', price=2499.99, quantity=15, 
                   description='High-performance laptop for professionals with M2 Pro chip'),
            Product(name='iMac 24"', category='Electronics', price=1299.99, quantity=8, 
                   description='All-in-one desktop computer with 4.5K display'),
            Product(name='iPad Pro 12.9"', category='Electronics', price=1099.99, quantity=25, 
                   description='Professional tablet with M2 chip and Liquid Retina XDR display'),
            Product(name='MacBook Air 13"', category='Electronics', price=999.99, quantity=20, 
                   description='Lightweight and powerful laptop with M2 chip'),
            Product(name='iPhone 15 Pro', category='Electronics', price=999.99, quantity=50, 
                   description='Latest smartphone with titanium design and advanced camera'),
            Product(name='AirPods Pro (2nd Gen)', category='Electronics', price=249.99, quantity=75, 
                   description='Wireless noise-cancelling earbuds with MagSafe Charging Case'),
            Product(name='Apple Watch Series 9', category='Electronics', price=399.99, quantity=30, 
                   description='Advanced smartwatch with health tracking and S9 chip'),
            Product(name='Gaming Laptop RTX 4070', category='Electronics', price=1799.99, quantity=8, 
                   description='High-performance gaming laptop with RGB keyboard and 144Hz display'),
            Product(name='Premium Cotton T-Shirt', category='Clothing', price=29.99, quantity=45, 
                   description='Comfortable 100% organic cotton t-shirt in various colors'),
            Product(name='Python Programming Book', category='Books', price=39.99, quantity=25, 
                   description='Complete guide to Python programming from beginner to advanced'),
            Product(name='Wireless Mechanical Keyboard', category='Electronics', price=129.99, quantity=15, 
                   description='Mechanical keyboard with RGB lighting and wireless connectivity'),
            Product(name='Noise Cancelling Headphones', category='Electronics', price=299.99, quantity=12, 
                   description='Over-ear headphones with active noise cancellation'),
            Product(name='Fitness Tracker Watch', category='Electronics', price=79.99, quantity=35, 
                   description='Waterproof fitness tracker with heart rate monitoring'),
            Product(name='Desk Lamp with Wireless Charger', category='Home', price=89.99, quantity=20, 
                   description='LED desk lamp with built-in wireless charging pad'),
            Product(name='Stainless Steel Water Bottle', category='Home', price=24.99, quantity=60, 
                   description='Insulated stainless steel water bottle, keeps drinks cold for 24 hours'),
        ]
        
        for product in sample_products:
            db.session.add(product)
        
        db.session.flush()  # Get product IDs
        
        # Create sample orders
        print("🛒 Creating sample orders...")
        sample_orders_data = [
            {
                'order_id': 'ORD202401001',
                'customer_name': 'John Smith',
                'customer_email': 'john.smith@email.com',
                'customer_phone': '+1-555-0101',
                'order_date': datetime(2024, 1, 15),
                'amount': 3749.98,
                'status': 'Delivered',
                'tracking_number': 'TRK789456123',
                'shipping_address': '123 Main Street, Apt 4B\nNew York, NY 10001\nUnited States',
                'notes': 'Customer requested signature confirmation',
                'items': [
                    {'product_id': 1, 'quantity': 1},  # MacBook Pro 16"
                    {'product_id': 5, 'quantity': 1}   # iPhone 15 Pro
                ]
            },
            {
                'order_id': 'ORD202401002', 
                'customer_name': 'Sarah Johnson',
                'customer_email': 'sarah.j@email.com',
                'customer_phone': '+1-555-0102',
                'order_date': datetime(2024, 1, 18),
                'amount': 1099.99,
                'status': 'Shipped',
                'tracking_number': 'TRK789456124',
                'shipping_address': '456 Oak Avenue\nLos Angeles, CA 90210\nUnited States',
                'notes': 'Gift wrapping requested',
                'items': [
                    {'product_id': 3, 'quantity': 1}   # iPad Pro
                ]
            },
            {
                'order_id': 'ORD202401003',
                'customer_name': 'Mike Wilson',
                'customer_email': 'mike.wilson@email.com', 
                'customer_phone': '+1-555-0103',
                'order_date': datetime(2024, 1, 20),
                'amount': 648.97,
                'status': 'Processing',
                'tracking_number': '',
                'shipping_address': '789 Pine Road\nChicago, IL 60601\nUnited States',
                'notes': 'Customer will pick up from store',
                'items': [
                    {'product_id': 6, 'quantity': 2},  # AirPods Pro
                    {'product_id': 10, 'quantity': 1}   # Python Book
                ]
            },
            {
                'order_id': 'ORD202401004',
                'customer_name': 'Emily Davis',
                'customer_email': 'emily.davis@email.com',
                'customer_phone': '+1-555-0104',
                'order_date': datetime(2024, 1, 22),
                'amount': 999.99,
                'status': 'Pending',
                'tracking_number': '',
                'shipping_address': '321 Elm Street\nHouston, TX 77001\nUnited States',
                'notes': 'Waiting for payment confirmation',
                'items': [
                    {'product_id': 4, 'quantity': 1}   # MacBook Air
                ]
            },
            {
                'order_id': 'ORD202401005',
                'customer_name': 'Robert Brown',
                'customer_email': 'robert.b@email.com',
                'customer_phone': '+1-555-0105',
                'order_date': datetime(2024, 1, 25),
                'amount': 399.99,
                'status': 'Delivered',
                'tracking_number': 'TRK789456125',
                'shipping_address': '654 Maple Drive\nPhoenix, AZ 85001\nUnited States',
                'notes': 'Left at front door as requested',
                'items': [
                    {'product_id': 7, 'quantity': 1}   # Apple Watch
                ]
            }
        ]
        
        for order_data in sample_orders_data:
            order = Order(
                order_id=order_data['order_id'],
                customer_name=order_data['customer_name'],
                customer_email=order_data['customer_email'],
                customer_phone=order_data['customer_phone'],
                order_date=order_data['order_date'],
                amount=order_data['amount'],
                status=order_data['status'],
                tracking_number=order_data['tracking_number'],
                shipping_address=order_data['shipping_address'],
                notes=order_data['notes']
            )
            db.session.add(order)
            db.session.flush()
            
            # Add order items and update product quantities
            for item_data in order_data['items']:
                product = Product.query.get(item_data['product_id'])
                if product:
                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=item_data['product_id'],
                        quantity=item_data['quantity'],
                        unit_price=product.price
                    )
                    db.session.add(order_item)
                    
                    # Update product stock (only for delivered/processing orders)
                    if order_data['status'] in ['Delivered', 'Shipped', 'Processing']:
                        product.quantity -= item_data['quantity']
        
        # Create sample sales data
        print("📈 Creating sample sales data...")
        for product in sample_products[:10]:  # Only for first 10 products
            for i in range(random.randint(3, 8)):
                sale = Sale(
                    product_id=product.id,
                    quantity_sold=random.randint(1, 3),
                    sale_price=product.price * random.uniform(0.85, 0.95),
                    sale_date=datetime(2024, 1, random.randint(1, 31))
                )
                db.session.add(sale)
        
        # Commit everything
        db.session.commit()
        
        print("\n✅ Database initialization complete!")
        print("📊 Sample data created:")
        print(f"   👤 Users: {User.query.count()}")
        print(f"   📦 Products: {Product.query.count()}")
        print(f"   🛒 Orders: {Order.query.count()}")
        print(f"   📈 Sales: {Sale.query.count()}")
        print(f"   📋 Order Items: {OrderItem.query.count()}")
        
        print("\n🔑 Demo credentials:")
        print("   Email: demo@example.com")
        print("   Password: password123")

# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------
UPLOAD_FOLDER = 'static/uploads/profile_images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------

def get_existing_categories():
    """Get all existing categories from the database"""
    categories = db.session.query(Product.category).distinct().all()
    return [category[0] for category in categories]

def get_dashboard_data():
    """Generate comprehensive dashboard data"""
    try:
        # Get all products
        products = Product.query.order_by(Product.created_at.desc()).all()
        
        # Product statistics
        total_products = len(products)
        total_stock = sum(p.quantity for p in products)
        out_of_stock = len([p for p in products if p.quantity == 0])
        
        # Sales data - now using Order model
        orders = Order.query.all()
        total_orders = len(orders)
        total_revenue = sum(order.amount for order in orders)
        
        # Customer count
        total_customers = User.query.count()
        
        # Recent orders - using the new Order model
        recent_orders = Order.query.order_by(Order.order_date.desc()).limit(5).all()
        
        # Category distribution - FIXED: Simple count only
        categories = {}
        for product in products:
            if product.category not in categories:
                categories[product.category] = 0  # Just store count as integer
            categories[product.category] += 1
        
        # Product performance data
        product_performance = [
            {'name': 'MacBook Pro 16"', 'percentage': 49},
            {'name': 'iMac 24"', 'percentage': 19},
            {'name': 'iPad Pro 12.9"', 'percentage': 29},
            {'name': 'MacBook Air 13"', 'percentage': 56}
        ]
        
        # Email statistics
        email_stats = [
            {'type': 'Marketing', 'percentage': 70},
            {'type': 'Promotions', 'percentage': 45},
            {'type': 'Newsletter', 'percentage': 45}
        ]
        
        # Delivery statistics based on actual order status
        status_counts = db.session.query(
            Order.status,
            db.func.count(Order.id).label('count')
        ).group_by(Order.status).all()
        
        total_order_count = sum(count for status, count in status_counts)
        delivery_stats = []
        for status, count in status_counts:
            percentage = int((count / total_order_count) * 100) if total_order_count > 0 else 0
            delivery_stats.append({
                'status': status,
                'percentage': percentage
            })
        
        # Monthly revenue data
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        income_data = [0] * 12  # Placeholder data
        expense_data = [0] * 12  # Placeholder data
        
        return {
            'products': products[:5],
            'total_products': total_products,
            'total_stock': total_stock,
            'out_of_stock': out_of_stock,
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'total_customers': total_customers,
            'recent_orders': recent_orders,
            'product_performance': product_performance,
            'email_stats': email_stats,
            'delivery_stats': delivery_stats,
            'categories': categories,  # Now this is simple category: count
            'months': months,
            'income_data': income_data,
            'expense_data': expense_data
        }
    except Exception as e:
        print(f"Error in get_dashboard_data: {e}")
        # Return default data if there's an error
        return {
            'products': [],
            'total_products': 0,
            'total_stock': 0,
            'out_of_stock': 0,
            'total_orders': 0,
            'total_revenue': 0,
            'total_customers': 0,
            'recent_orders': [],
            'product_performance': [],
            'email_stats': [],
            'delivery_stats': [],
            'categories': {},
            'months': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            'income_data': [0] * 12,
            'expense_data': [0] * 12
        }

# ------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------

@app.route('/')
def home():
    return redirect(url_for('login'))

# ------------------------- Authentication -------------------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_email'] = user.email
            session['user_image'] = user.image_url
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
       
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered! Please use a different email.', 'error')
            return render_template('register.html')
       
        new_user = User(name=name, email=email)
        new_user.set_password(password)
       
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Error creating account. Please try again.', 'error')
   
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

# ------------------------- Dashboard -----------------------------------------

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
   
    dashboard_data = get_dashboard_data()
    return render_template('dashboard.html', **dashboard_data)

# ------------------------- Order Management ---------------------------------

@app.route('/orders')
def orders():
    if 'user_id' not in session:
        return redirect(url_for('login'))
   
    orders_list = Order.query.order_by(Order.order_date.desc()).all()
    return render_template('recent_orders.html', orders=orders_list)

@app.route('/create_order', methods=['GET', 'POST'])
def create_order():
    if 'user_id' not in session:
        return redirect(url_for('login'))
   
    products = Product.query.all()
    
    if request.method == 'POST':
        try:
            # Generate unique order ID
            order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Create order
            new_order = Order(
                order_id=order_id,
                customer_name=request.form['customer_name'],
                customer_email=request.form.get('customer_email', ''),
                customer_phone=request.form.get('customer_phone', ''),
                order_date=datetime.strptime(request.form['order_date'], '%Y-%m-%d'),
                amount=0,  # Will calculate from items
                status=request.form['status'],
                tracking_number=request.form.get('tracking_number', ''),
                shipping_address=request.form.get('shipping_address', ''),
                notes=request.form.get('notes', '')
            )
            
            db.session.add(new_order)
            db.session.flush()  # Get the order ID
            
            # Process order items
            total_amount = 0
            product_ids = request.form.getlist('product_id[]')
            quantities = request.form.getlist('quantity[]')
            
            for i, (product_id, quantity_str) in enumerate(zip(product_ids, quantities)):
                if not product_id or not quantity_str:
                    continue
                    
                product = Product.query.get(int(product_id))
                quantity = int(quantity_str)
                
                if product and quantity > 0:
                    # Check stock availability
                    if product.quantity < quantity:
                        flash(f'Not enough stock for {product.name}. Available: {product.quantity}', 'error')
                        db.session.rollback()
                        return render_template('add_order.html', products=products)
                    
                    # Create order item
                    order_item = OrderItem(
                        order_id=new_order.id,
                        product_id=product.id,
                        quantity=quantity,
                        unit_price=product.price
                    )
                    
                    db.session.add(order_item)
                    total_amount += product.price * quantity
                    
                    # Update product stock
                    product.quantity -= quantity
            
            # Update order total amount
            new_order.amount = total_amount
            
            db.session.commit()
            flash(f'Order {order_id} created successfully!', 'success')
            return redirect(url_for('orders'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating order: {str(e)}', 'error')
    
    return render_template('add_order.html', products=products, datetime=datetime)

@app.route('/edit_order/<int:order_id>', methods=['GET', 'POST'])
def edit_order(order_id):
    if 'user_id' not in session:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Not authenticated'})
        return redirect(url_for('login'))
   
    order = Order.query.get_or_404(order_id)
    
    if request.method == 'POST':
        try:
            # Check if it's a JSON request (from recent-orders modal)
            if request.is_json:
                data = request.get_json()
                order.customer_name = data['customerName']
                order.customer_email = data['customerEmail']
                order.order_date = datetime.strptime(data['orderDate'], '%Y-%m-%d')
                order.amount = data['orderAmount']
                order.status = data['orderStatus']
                
                db.session.commit()
                return jsonify({'success': True, 'message': 'Order updated successfully!'})
            else:
                # Regular form submission (from edit-order page)
                order.customer_name = request.form['customerName']
                order.customer_email = request.form.get('customerEmail', '')
                order.customer_phone = request.form.get('customerPhone', '')
                order.order_date = datetime.strptime(request.form['orderDate'], '%Y-%m-%d')
                order.status = request.form['orderStatus']
                order.tracking_number = request.form.get('trackingNumber', '')
                order.shipping_address = request.form.get('shippingAddress', '')
                order.notes = request.form.get('orderNotes', '')
                order.amount = float(request.form.get('orderAmount', order.amount))
                
                db.session.commit()
                flash('Order updated successfully!', 'success')
                return redirect(url_for('recent_orders'))
            
        except Exception as e:
            db.session.rollback()
            if request.is_json:
                return jsonify({'success': False, 'message': f'Error updating order: {str(e)}'})
            else:
                flash(f'Error updating order: {str(e)}', 'error')
    
    # For GET requests, render the edit form
    return render_template('edit_order.html', order=order)

@app.route('/delete_order/<int:order_id>', methods=['POST'])
def delete_order(order_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
   
    try:
        order = Order.query.get_or_404(order_id)
        order_id_str = order.order_id
        
        # Restore product quantities
        for item in order.items:
            product = Product.query.get(item.product_id)
            if product:
                product.quantity += item.quantity
        
        db.session.delete(order)
        db.session.commit()
        return jsonify({'success': True, 'message': f'Order {order_id_str} deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error deleting order: {str(e)}'})

@app.route('/order_details/<int:order_id>')
def order_details(order_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
   
    order = Order.query.get_or_404(order_id)
    return render_template('order_details.html', order=order)

# ------------------------- Product Management ---------------------------------

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if 'user_id' not in session:
        return redirect(url_for('login'))
   
    existing_categories = get_existing_categories()
    
    if request.method == 'POST':
        try:
            name = request.form['name'].strip()
            category = request.form['category'].strip()
            price = float(request.form['price'])
            quantity = int(request.form['quantity'])
            description = request.form.get('description', '').strip()
            
            # Validate inputs
            if not name:
                flash('Product name cannot be empty!', 'error')
                return render_template('add_product.html', existing_categories=existing_categories)
            
            if not category:
                flash('Category cannot be empty!', 'error')
                return render_template('add_product.html', existing_categories=existing_categories)
            
            if price < 0:
                flash('Price cannot be negative!', 'error')
                return render_template('add_product.html', existing_categories=existing_categories)
            
            if quantity < 0:
                flash('Quantity cannot be negative!', 'error')
                return render_template('add_product.html', existing_categories=existing_categories)
           
            # Capitalize first letter of category for consistency
            category = category[0].upper() + category[1:].lower() if category else category
           
            # Check if product with same name already exists (optional)
            existing_product = Product.query.filter_by(name=name).first()
            if existing_product:
                flash(f'Product "{name}" already exists! You can edit it from the inventory.', 'warning')
                return redirect(url_for('edit_product', product_id=existing_product.id))
           
            new_product = Product(
                name=name,
                category=category,
                price=price,
                quantity=quantity,
                description=description
            )

            db.session.add(new_product)
            db.session.commit()
            flash(f'Product "{name}" added to category "{category}" successfully!', 'success')
            return redirect(url_for('inventory'))
        except ValueError:
            db.session.rollback()
            flash('Invalid price or quantity format. Please enter valid numbers.', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding product: {str(e)}', 'error')

    return render_template('add_product.html', existing_categories=existing_categories)


@app.route('/inventory')
def inventory():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    products = Product.query.order_by(Product.created_at.desc()).all()
    # Get unique categories for the filter dropdown
    categories = db.session.query(Product.category).distinct().all()
    categories = [category[0] for category in categories if category[0]]  # Remove any None values

    return render_template('inventory.html', products=products, categories=categories)


@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)

    # Get unique categories for the dropdown
    existing_categories = db.session.query(Product.category).distinct().all()
    existing_categories = [cat[0] for cat in existing_categories]

    if request.method == 'POST':
        # Update product logic here
        product.name = request.form['name']
        product.description = request.form['description']
        product.category = request.form['category']
        product.price = float(request.form['price'])
        product.quantity = int(request.form['quantity'])
        
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('inventory'))
    
    return render_template('edit_product.html', product=product, existing_categories=existing_categories)

@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
   
    try:
        product = Product.query.get_or_404(product_id)
        product_name = product.name
        
        # Delete related records first to avoid foreign key constraints
        OrderItem.query.filter_by(product_id=product_id).delete()
        Sale.query.filter_by(product_id=product_id).delete()
        
        # Now delete the product
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Product "{product_name}" deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting product: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'Error deleting product: {str(e)}'
        })

# ------------------------- Reports -------------------------------------------

@app.route('/report')
def report():
    if 'user_id' not in session:
        return redirect(url_for('login'))
   
    products = Product.query.all()
    total_count = len(products)
    total_value = sum(p.price * p.quantity for p in products)
   
    categories = {}
    for p in products:
        if p.category not in categories:
            categories[p.category] = {'count': 0, 'value': 0}
        categories[p.category]['count'] += 1
        categories[p.category]['value'] += p.price * p.quantity
   
    low_stock_items = Product.query.filter(Product.quantity < 10).all()
    
    # Convert Product objects to dictionaries for JSON serialization
    low_stock_items_dict = []
    for item in low_stock_items:
        low_stock_items_dict.append({
            'id': item.id,
            'name': item.name,
            'category': item.category,
            'price': float(item.price),
            'quantity': item.quantity,
            'description': item.description
        })
    
    # Calculate highest value category for the report
    highest_value_category = ['', {'value': 0}]
    if categories:
        highest_value_category = max(categories.items(), key=lambda x: x[1]['value'])
    
    # Calculate category statistics
    category_stats = {
        'count': len(categories),
        'highest_value': {
            'name': highest_value_category[0],
            'value': highest_value_category[1]['value']
        },
        'total_value': total_value
    }
    
    # Calculate low stock statistics
    low_stock_stats = {
        'total': len(low_stock_items),
        'out_of_stock': len([p for p in low_stock_items if p.quantity == 0]),
        'low_stock': len([p for p in low_stock_items if p.quantity > 0 and p.quantity < 10])
    }

    return render_template(
        'report.html',
        total_count=total_count,
        total_value=total_value,
        categories=categories,
        low_stock_items=low_stock_items,
        low_stock_items_dict=low_stock_items_dict,
        now=datetime.now(),
        category_stats=category_stats,
        low_stock_stats=low_stock_stats,
        highest_value_category=highest_value_category
    )

@app.route('/reset-db')
def reset_db_route():
    """Reset the database to a clean state."""
    try:
        init_database()
        flash('Database has been successfully reset.', 'success')
    except Exception as e:
        flash(f'Error resetting database: {e}', 'danger')
    return redirect(url_for('dashboard'))

# ------------------------- Recent Orders Page --------------------------------

@app.route('/recent-orders')
def recent_orders():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    orders_data = Order.query.order_by(Order.order_date.desc()).all()
    return render_template('recent_orders.html', orders=orders_data)

# ------------------------- Add Order Page ------------------------------------

@app.route('/add-order')
def add_order():
    return render_template('add_order.html')

# ------------------------------------------------------------------------------
# Run App
# ------------------------------------------------------------------------------

if __name__ == '__main__':
    # Initialize database
    print("🚀 Starting Inventory Management System...")
    init_database()

    print("🌐 Access the application at: http://localhost:5000")
    print("🔑 Demo credentials: demo@example.com / password123")
    app.run(debug=True)