import os

port = int(os.getenv("PORT", 10000))
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
