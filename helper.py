from ultralytics import YOLO
import cv2
import time
import numpy as np
from pymongo import MongoClient
from datetime import datetime, timezone
from urllib.parse import quote_plus
import threading

# MongoDB Setup
username = quote_plus("dustbin")  # Replace with your MongoDB username
password = quote_plus("Dustbin@123")  # Replace with your MongoDB password
MONGO_URI = f"mongodb+srv://{username}:{password}@cluster0.fmudd.mongodb.net/"
DATABASE_NAME = "garbage_detection"

# Connect to MongoDB
try:
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client[DATABASE_NAME]
    detections_collection_cam1 = db["detections"]
    detections_collection_cam2 = db["other_model_detection"]

    # Set TTL (Time to Live) for collections
    detections_collection_cam1.create_index("timestamp", expireAfterSeconds=7200)
    detections_collection_cam2.create_index("timestamp", expireAfterSeconds=7200)

    print("Connected to MongoDB successfully.")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    exit()

# Function to insert detection data into MongoDB
def insert_detection_data(collection, data):
    try:
        collection.insert_one(data)
        print(f"Detection data saved to MongoDB ({collection.name}).")
    except Exception as e:
        print(f"Error saving data to MongoDB ({collection.name}): {e}")

# Load YOLO models
# garbage_model = YOLO("Garbage_v2.pt")
polythene_nonpoly_model = YOLO("poly_non_poly.pt")
bio_nonBio_model = YOLO("biogas.pt")

# Constants
ESP32_CAM_URL_1 = "http://192.168.1.104/capture.jpg"  # Camera 1 URL
ESP32_CAM_URL_2 = "http://192.168.1.3/cam-hi.jpg"  # Camera 2 URL
fps_limit = 30  # Adjust FPS limit to balance performance
last_frame_time = 0


# Function to fetch a frame from the camera with OpenCV
def fetch_frame(camera_url):
    try:
        # Use OpenCV to capture the frame from the camera URL
        cap = cv2.VideoCapture(camera_url)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            if ret:
                return frame
        print(f"Error fetching frame from {camera_url}.")
    except Exception as e:
        print(f"Error fetching frame: {e}")
    return None

# Function to process Camera 2 feed and return frames for Flask to display
def process_camera1():
    global last_frame_time
    while True:
        current_time = time.time()
        if current_time - last_frame_time < 1 / fps_limit:
            time.sleep(0.01)
            continue

        # Fetch frame from camera
        frame = fetch_frame(ESP32_CAM_URL_1)
        if frame is None:
            print("Failed to fetch frame from Camera 2.")
            time.sleep(0.5)
            continue

        # Downscale frame for faster processing (optional)
        frame = cv2.resize(frame, (640, 480))  # Adjust size as needed

        # Detect bio or non-bio garbage
        poly_results = polythene_nonpoly_model.predict(source=frame, conf=0.50, show=False)
        for result in poly_results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = box.conf[0].item()
                class_id = box.cls[0].item()

                if conf < 0.50:
                    continue

                # Detected bio or non-bio object
                object_name = polythene_nonpoly_model.names[int(class_id)]

                # Save detection data to MongoDB
                detection_data = {
                    "camera": "camera1",
                    "object": object_name,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                insert_detection_data(detections_collection_cam1, detection_data)

                # Draw bounding box and labels
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"{object_name} ({int(conf * 100)}%)", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        # Encode frame as JPEG image
        ret, jpeg = cv2.imencode('.jpg', frame)
        if not ret:
            return None
        return jpeg.tobytes()


# Function to process Camera 2 feed and return frames for Flask to display
def process_camera2():
    global last_frame_time
    while True:
        current_time = time.time()
        if current_time - last_frame_time < 1 / fps_limit:
            time.sleep(0.01)
            continue

        # Fetch frame from camera
        frame = fetch_frame(ESP32_CAM_URL_2)
        if frame is None:
            print("Failed to fetch frame from Camera 2.")
            time.sleep(0.5)
            continue

        # Downscale frame for faster processing (optional)
        frame = cv2.resize(frame, (640, 480))  # Adjust size as needed

        # Detect bio or non-bio garbage
        bio_results = bio_nonBio_model.predict(source=frame, conf=0.50, show=False)
        for result in bio_results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = box.conf[0].item()
                class_id = box.cls[0].item()

                if conf < 0.50:
                    continue

                # Detected bio or non-bio object
                object_name = bio_nonBio_model.names[int(class_id)]

                # Save detection data to MongoDB
                detection_data = {
                    "camera": "camera2",
                    "object": object_name,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                insert_detection_data(detections_collection_cam2, detection_data)

                # Draw bounding box and labels
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"{object_name} ({int(conf * 100)}%)", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        # Encode frame as JPEG image
        ret, jpeg = cv2.imencode('.jpg', frame)
        if not ret:
            return None
        return jpeg.tobytes()
