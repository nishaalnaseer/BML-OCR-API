#!/bin/bash

git pull
sudo docker exec ocr rm -rf /app/src
sudo docker exec ocr rm /app/main.py

sudo docker cp src/ ocr:/app/src/
sudo docker cp main.py ocr:/app/

sudo docker restart ocr