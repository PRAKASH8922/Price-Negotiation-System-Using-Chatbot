import os
import sys
import argparse
import pymysql

# Add the current directory to Python path to import Django settings
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Define default passwords to attempt connecting automatically
DEFAULT_PASSWORDS = [
    '', 'root', 'admin', 'password', 'root123', 'root1234', '123456', '1234',
    '12345678', 'mysql', 'root@123', 'admin123', 'Admin@123', 'Admin123',
    'prakash', 'prakash123', 'Prakash@123', 'Prakash123', 'prakash8922',
    'Prakash8922', 'Prakash@8922', 'prakash@8922'
]

def find_working_connection(user='root', host='127.0.0.1', port=3306, override_pwd=None):
    if override_pwd is not None:
        try:
            conn = pymysql.connect(host=host, user=user, password=override_pwd, port=port, connect_timeout=2)
            print(f"Successfully connected to MySQL using provided password.")
            return conn, override_pwd
        except Exception as e:
            print(f"Error: Connection with provided password failed: {e}")
            return None, None

    for p in DEFAULT_PASSWORDS:
        try:
            conn = pymysql.connect(host=host, user=user, password=p, port=port, connect_timeout=1)
            print(f"Successfully connected to MySQL using default password '{p}'")
            return conn, p
        except Exception:
            continue
    return None, None

def update_settings_file(password):
    settings_path = os.path.join('PriceNegotiationSystem', 'settings.py')
    if not os.path.exists(settings_path):
        print("Error: settings.py not found!")
        return False
    
    with open(settings_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace the default password in the MySQL DATABASES settings block
    target = "'PASSWORD': 'root',"
    replacement = f"'PASSWORD': '{password}',"
    
    if target in content:
        content = content.replace(target, replacement)
    else:
        import re
        content = re.sub(r"'PASSWORD':\s*'[^']*',", f"'PASSWORD': '{password}',", content)

    with open(settings_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Updated password in settings.py.")
    return True

def create_database(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS price_negotiation_db;")
        print("Database 'price_negotiation_db' is ready.")
        cursor.close()
        return True
    except Exception as e:
        print(f"Failed to create database: {e}")
        return False

def seed_data():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PriceNegotiationSystem.settings')
    try:
        import django
        django.setup()
    except Exception as e:
        print(f"Failed to setup Django configuration: {e}")
        return

    from django.contrib.auth.models import User
    from negotiation_app.models import Category, Product

    print("\n--- Seeding Database ---")

    # 1. Create Superuser (if not exists)
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        print("Superuser created successfully: (Username: 'admin', Password: 'admin123')")
    else:
        print("Superuser 'admin' already exists.")

    # 2. Seed Categories and Products
    data = {
        'Electronics': [
            {'name': 'Premium Laptop', 'desc': 'High-performance laptop for coding and design.', 'price': 999.00, 'is_offer': False, 'min_price': 890.00},
            {'name': 'Smartphone X', 'desc': 'Latest flagship smartphone with AMOLED display.', 'price': 699.00, 'is_offer': False, 'min_price': 630.00},
            {'name': 'Wireless Headphones', 'desc': 'Active noise-cancelling over-ear headphones.', 'price': 199.00, 'is_offer': False, 'min_price': 165.00},
            {'name': 'Mechanical Keyboard', 'desc': 'RGB backlit gaming keyboard. (Special Promo)', 'price': 79.99, 'is_offer': True, 'min_price': 79.99},
            {'name': 'Ergonomic Wireless Mouse', 'desc': 'Comfortable wireless office mouse. (Clearance Sale)', 'price': 29.99, 'is_offer': True, 'min_price': 29.99},
        ],
        'Fashion': [
            {'name': 'Classic Leather Jacket', 'desc': 'Genuine black leather jacket, durable and stylish.', 'price': 149.00, 'is_offer': False, 'min_price': 120.00},
            {'name': 'Running Sneakers', 'desc': 'Lightweight and breathable active running shoes.', 'price': 89.00, 'is_offer': False, 'min_price': 75.00},
            {'name': 'Polarized Sunglasses', 'desc': 'UV protection retro design sunglasses.', 'price': 49.00, 'is_offer': False, 'min_price': 40.00},
            {'name': 'Cotton Summer T-Shirt', 'desc': '100% organic cotton breathable t-shirt. (Special Deal)', 'price': 19.99, 'is_offer': True, 'min_price': 19.99},
            {'name': 'Slim Fit Denim Jeans', 'desc': 'Classic blue stretchable denim jeans. (Discount Offer)', 'price': 39.99, 'is_offer': True, 'min_price': 39.99},
        ],
        'Home & Kitchen': [
            {'name': 'Drip Coffee Maker', 'desc': 'Programmable 12-cup glass carafe coffee maker.', 'price': 79.00, 'is_offer': False, 'min_price': 65.00},
            {'name': 'Digital Air Fryer', 'desc': 'Large capacity hot air cooker for healthy meals.', 'price': 119.00, 'is_offer': False, 'min_price': 100.00},
            {'name': 'High-Speed Blender', 'desc': 'Multi-function blender for smoothies and shakes.', 'price': 59.00, 'is_offer': False, 'min_price': 50.00},
            {'name': 'Stainless Steel Chef Knife', 'desc': 'Professional-grade 8-inch kitchen knife. (Promo Price)', 'price': 24.99, 'is_offer': True, 'min_price': 24.99},
            {'name': '2-Slice Bread Toaster', 'desc': 'Compact stainless steel toaster. (Clearance Discount)', 'price': 19.99, 'is_offer': True, 'min_price': 19.99},
        ]
    }

    image_placeholders = {
        'Electronics': 'https://images.unsplash.com/photo-1498049794561-7780e7231661?w=500&auto=format&fit=crop&q=60',
        'Fashion': 'https://images.unsplash.com/photo-1483985988355-763728e1935b?w=500&auto=format&fit=crop&q=60',
        'Home & Kitchen': 'https://images.unsplash.com/photo-1556911220-e15b29be8c8f?w=500&auto=format&fit=crop&q=60'
    }

    for cat_name, products in data.items():
        category, created = Category.objects.get_or_create(name=cat_name, defaults={'description': f'Products related to {cat_name}'})
        if created:
            print(f"Created category: {cat_name}")
        else:
            print(f"Category already exists: {cat_name}")

        for p_info in products:
            img = image_placeholders.get(cat_name)
            product, p_created = Product.objects.get_or_create(
                name=p_info['name'],
                category=category,
                defaults={
                    'description': p_info['desc'],
                    'price': p_info['price'],
                    'is_offer': p_info['is_offer'],
                    'min_negotiation_price': p_info['min_price'],
                    'image_url': img
                }
            )
            if p_created:
                print(f"  Inserted product: {product.name} (Offer: {product.is_offer}, Price: ${product.price}, Min: ${product.min_negotiation_price})")
            else:
                print(f"  Product already exists: {product.name}")

    print("\nDatabase seeded successfully!")

def main(args_list=None):
    parser = argparse.ArgumentParser(description="Configure MySQL and seed data for Price Negotiation System.")
    parser.add_argument('--password', type=str, default=None, help="MySQL root password")
    args = parser.parse_args(args_list)

    using_mysql = False
    print("Checking connection to MySQL local server...")
    
    # Quick socket check to see if port 3306 is open before trying database connections
    import socket
    port_open = False
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect(('127.0.0.1', 3306))
        s.close()
        port_open = True
    except Exception:
        pass

    conn, password = None, None
    if port_open or args.password is not None:
        conn, password = find_working_connection(override_pwd=args.password)
    
    if conn:
        # 1. Create database
        db_created = create_database(conn)
        conn.close()
        if db_created:
            # 2. Update settings.py
            update_settings_file(password)
            using_mysql = True
            print("Successfully configured MySQL.")
    
    if not using_mysql:
        print("\n" + "="*80)
        print("WARNING: Could not connect to MySQL. Falling back to SQLite for database setup.")
        print("To switch to MySQL later, make sure MySQL is running and execute:")
        print("  python setup_db.py --password YOUR_MYSQL_PASSWORD")
        print("="*80 + "\n")

    # 3. Run Migrations and setup Django
    print("\n--- Running Migrations ---")
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PriceNegotiationSystem.settings')
    import django
    django.setup()
    
    from django.core.management import call_command
    try:
        call_command("makemigrations", "negotiation_app", interactive=False)
        call_command("migrate", interactive=False)
    except Exception as e:
        print(f"Error applying migrations: {e}")
        raise e

    # 4. Seed database
    seed_data()
    print("\n" + "="*80)
    print("Setup completed successfully!")
    print("Run the server using: python manage.py runserver")
    print("Admin details: Username: admin, Password: admin123")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
