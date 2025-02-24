import os

port = os.getenv('PORT', '8000')
bind = f"0.0.0.0:{port}"
workers = 4
threads = 4
worker_class = "gthread"
timeout = 120
keepalive = 5
errorlog = "-"
accesslog = "-"
capture_output = True
enable_stdio_inheritance = True
