import os

# Configurações básicas
port = os.getenv('PORT', '8000')
bind = f"0.0.0.0:{port}"

# Configurações de workers
workers = 2  # Reduzido para 2 workers
threads = 2  # Reduzido para 2 threads por worker
worker_class = "gthread"
worker_connections = 1000

# Timeouts
timeout = 120
keepalive = 5

# Logging
loglevel = "info"
errorlog = "-"
accesslog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Outros
capture_output = True
enable_stdio_inheritance = True
graceful_timeout = 120
max_requests = 1000
max_requests_jitter = 50
