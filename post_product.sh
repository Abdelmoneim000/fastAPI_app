#!/usr/bin/env bash

curl -X POST "http://127.0.0.1:8000/products/" \
     -H "Content-Type: application/json" \
     -d '{"name": "Laptop", "description": "A powerful gaming laptop", "price": 1500}'
