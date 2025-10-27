#!/bin/bash
gunicorn petri_dish.run:app --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT
