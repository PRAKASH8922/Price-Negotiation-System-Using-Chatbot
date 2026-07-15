# Gunicorn configuration file for production hosting

import os

# Port and Bind Address
# Render/Railway injects a PORT environment variable, defaulting to 8000
port = os.environ.get("PORT", "8000")
bind = f"0.0.0.0:{port}"

# Worker Processes
# Recommended formula: 2-4 workers per CPU core
workers = 2
threads = 4
timeout = 120

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = "info"

# Process Naming
proc_name = "price_negotiation_system"
