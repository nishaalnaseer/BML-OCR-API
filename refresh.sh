#!/bin/bash

git pull
sudo docker exec ocr rm -rf /app/src
sudo docker exec ocr rm /app/main.py

sudo docker cp src/ ocr:/app/src/
sudo docker exec ocr rm -rf /app/tests
sudo docker cp tests/ ocr:/app/tests/

sudo docker restart ocr
