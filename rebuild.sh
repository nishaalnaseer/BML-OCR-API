#!/bin/bash

sudo git pull
sudo docker rmi ocr -f
sudo docker build -t ocr .

sudo docker rm ocr -f
sudo docker run -itd --restart=always --name ocr --network host  ocr
