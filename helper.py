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
DATABASE_NAME = "Detection"

# Connect to MongoDB
try:
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client[DATABASE_NAME]
    
    # Collections for different sensors
    ultrasonic_collection = db["ultrasonic_data"]
    polythene_collection = db["polythene_data"]
    bio_collection = db["bio_data"]

    # Set TTL (Time to Live) for collections (Data expires after 2 hours)
    ultrasonic_collection.create_index("timestamp", expireAfterSeconds=7200)
    polythene_collection.create_index("timestamp", expireAfterSeconds=7200)
    bio_collection.create_index("timestamp", expireAfterSeconds=7200)

    print("Connected to MongoDB successfully.")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    exit()

# Function to insert detection data into MongoDB
def insert_detection_data(collection, data):
    try:
        collection.insert_one(data)
        print(f"Data saved to MongoDB ({collection.name}).")
    except Exception as e:
        print(f"Error saving data to MongoDB ({collection.name}): {e}")

# Load YOLO models
polythene_nonpoly_model = YOLO("poly_non_poly.pt")
bio_nonBio_model = YOLO("biogas.pt")

# Constants
ESP32_CAM_URL_1 = "http://192.168.1.104/capture.jpg"  # Camera 1 URL
ESP32_CAM_URL_2 = "http://192.168.1.104/capture.jpg"  # Camera 2 URL
fps_limit = 30  # Adjust FPS limit to balance performance
last_frame_time = 0

# Function to process ultrasonic sensor data and save it to MongoDB
def process_ultrasonic_data(flag, timestamp, distance):
    if flag not in [0, 1]:
        return {"error": "Invalid flag value. Must be 0 or 1."}, 400

    detection_data = {
        "flag": flag,
        "timestamp": datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S"),
        "distance": distance
    }

    # Insert data into MongoDB and get the inserted document ID
    inserted_doc = ultrasonic_collection.insert_one(detection_data)
    
    # Return the response with inserted document ID (ObjectId converted to string for JSON serialization)
    response_data = {
        "_id": str(inserted_doc.inserted_id),
        "flag": flag,
        "timestamp": timestamp,
        "distance": distance
    }
    
    return response_data, 200


# ✅ Function to fetch a frame from the camera with OpenCV
def fetch_frame(camera_url):
    try:
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

# ✅ Function to process Camera 1 feed (Polythene Detection)
# ✅ Function to process Camera 1 feed (Polythene Detection)
def process_camera1():
    global last_frame_time
    while True:
        current_time = time.time()
        if current_time - last_frame_time < 1 / fps_limit:
            time.sleep(0.01)
            continue

        frame = fetch_frame(ESP32_CAM_URL_1)
        if frame is None:
            print("Failed to fetch frame from Camera 1.")
            time.sleep(0.5)
            continue

        frame = cv2.resize(frame, (640, 480))

        poly_results = polythene_nonpoly_model.predict(source=frame, conf=0.50, show=False)
        for result in poly_results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = box.conf[0].item()
                class_id = box.cls[0].item()

                if conf < 0.50:
                    continue

                object_name = polythene_nonpoly_model.names[int(class_id)]

                # Add the detection column for polythene detection (1 if detected)
                detection_status = 1 if object_name.lower() == "polythene" else 0

                detection_data = {
                    "camera": "camera1",
                    "object": object_name,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "polythene_detected": detection_status  # New column to store detection status
                }

                # Print the detection status for polythene
                if detection_status == 1:
                    print(f"Polythene detected! Detection Status: {detection_status}")

                # Insert the detection data into MongoDB
                insert_detection_data(polythene_collection, detection_data)

                # Draw bounding box and label on the frame
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"{object_name} ({int(conf * 100)}%)", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        ret, jpeg = cv2.imencode('.jpg', frame)
        if not ret:
            return None
        return jpeg.tobytes()


# ✅ Function to process Camera 2 feed (Bio vs. Non-Bio Detection)
def process_camera2():
    global last_frame_time
    while True:
        current_time = time.time()
        if current_time - last_frame_time < 1 / fps_limit:
            time.sleep(0.01)
            continue

        frame = fetch_frame(ESP32_CAM_URL_2)
        if frame is None:
            print("Failed to fetch frame from Camera 2.")
            time.sleep(0.5)
            continue

        frame = cv2.resize(frame, (640, 480))

        bio_results = bio_nonBio_model.predict(source=frame, conf=0.50, show=False)
        for result in bio_results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = box.conf[0].item()
                class_id = box.cls[0].item()

                if conf < 0.50:
                    continue

                object_name = bio_nonBio_model.names[int(class_id)]

                detection_data = {
                    "camera": "camera2",
                    "object": object_name,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                insert_detection_data(bio_collection, detection_data)

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"{object_name} ({int(conf * 100)}%)", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        ret, jpeg = cv2.imencode('.jpg', frame)
        if not ret:
            return None
        return jpeg.tobytes()
