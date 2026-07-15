"""
WSGI config for PriceNegotiationSystem project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys
import sqlite3
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PriceNegotiationSystem.settings')

# Run migrations and database setup on startup if database is not ready
try:
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(root_dir, 'db.sqlite3')
    lock_file = os.path.join(root_dir, 'db_setup.lock')
    
    run_setup = True
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='negotiation_app_category';")
            if cursor.fetchone():
                run_setup = False
            conn.close()
        except Exception:
            pass

    # Avoid duplicate execution across workers using a simple file lock check
    if run_setup and not os.path.exists(lock_file):
        # Create lock file
        try:
            with open(lock_file, 'w') as f:
                f.write('locked')
        except Exception:
            pass
            
        print("Running startup database checks and migrations...")
        if root_dir not in sys.path:
            sys.path.append(root_dir)
        import setup_db
        setup_db.main([])
        print("Startup database check completed successfully.")
        
        # Remove lock file
        try:
            os.remove(lock_file)
        except Exception:
            pass
except Exception as e:
    print(f"Error running database setup on startup: {e}")

application = get_wsgi_application()
