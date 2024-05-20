#!/bin/bash

sudo docker rmi ocr -f
sudo docker rm ocr -f

sudo docker build -t ocr .

sudo docker run -itd --restart=always --name ocr --network host  ocr
