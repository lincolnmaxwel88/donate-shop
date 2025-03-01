#!/bin/bash
python init_db.py
gunicorn -c gunicorn_config.py app:app
