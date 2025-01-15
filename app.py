from flask import Flask, Response
from helper import *
from ultralytics import YOLO
import cv2
import time
import numpy as np
from pymongo import MongoClient
from datetime import datetime, timezone
from urllib.parse import quote_plus
import requests

# Initialize Flask app
app = Flask(__name__)

# Video stream routes
@app.route('/camera1_feed')
def camera1_feed():
    return Response(process_camera1(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/camera2_feed')
def camera2_feed():
    return Response(process_camera2(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True, host='192.168.1.50', port=5000)  # Use specific host IP
