# gunicorn_config.py
import multiprocessing

max_requests = 1000
max_requests_jitter = 50
workers = multiprocessing.cpu_count()
bind = "0.0.0.0:8080"  # Address and port to bind Gunicorn

