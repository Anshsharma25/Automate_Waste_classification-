from ultralytics import YOLO
import cv2
import time
import numpy as np
from pymongo import MongoClient
from datetime import datetime, timezone
from urllib.parse import quote_plus
import requests

# MongoDB Setup
username = quote_plus("dustbin")  # Replace with MongoDB username
password = quote_plus("Dustbin@123")  # Replace with MongoDB password
MONGO_URI = f"mongodb+srv://{username}:{password}@cluster0.fmudd.mongodb.net/"
DATABASE_NAME = "garbage_detection"

# Connect to MongoDB
try:
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client[DATABASE_NAME]
    # Collections for different cameras
    detections_collection_cam1 = db["detections"]
    detections_collection_cam2 = db["Other_model_detection"]

    # Set TTL for collections
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
garbage_model = YOLO("garbage_model_path.pt")
#cover_noncover_model = YOLO("cover_noncover_model_path.pt")
polythene_nonpoly_model = YOLO("polythene_nonpoly_model_path.pt")
#dry_wet_model = YOLO("dry_wet_model_path.pt")
bio_nonBio_model = YOLO("bio_nonBio_model_path.pt")

# Constants
ESP32_CAM_URL_1 = "http://192.168.1.100/cam-hi.jpg"  # Camera 1
ESP32_CAM_URL_2 = "http://192.168.1.101/cam-hi.jpg"  # Camera 2
fps_limit = 40
last_frame_time = 0

# Fetch frame from the camera
def fetch_frame(camera):
    url = ESP32_CAM_URL_1 if camera == 1 else ESP32_CAM_URL_2
    try:
        response = requests.get(url, stream=True, timeout=5)
        if response.status_code == 200:
            img_array = np.asarray(bytearray(response.content), dtype=np.uint8)
            return cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    except Exception as e:
        print(f"Error fetching frame from Camera {camera}: {e}")
    return None

# Process Camera 1 Feed
def process_camera1():
    global last_frame_time

    while True:
        current_time = time.time()
        if current_time - last_frame_time < 1 / fps_limit:
            time.sleep(0.01)
            continue

        frame = fetch_frame(camera=1)
        if frame is None:
            print("Failed to fetch frame from Camera 1.")
            time.sleep(0.5)
            continue

        # Detect garbage
        garbage_results = garbage_model.predict(source=frame, conf=0.5, show=False)
        for result in garbage_results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = box.conf[0].item()
                class_id = box.cls[0].item()

                if conf < 0.5:
                    continue

                object_name = garbage_model.names[int(class_id)]
                cropped_garbage = frame[y1:y2, x1:x2]

                '''# Detect cover or uncover status
                cover_results = cover_noncover_model.predict(source=cropped_garbage, conf=0.5, show=False)
                cover_class = None
                if cover_results and cover_results[0].boxes:
                    cover_class = cover_noncover_model.names[int(cover_results[0].boxes[0].cls[0])]'''

                # Detect polythene or non-polythene
                poly_results = polythene_nonpoly_model.predict(source=cropped_garbage, conf=0.7, show=False)
                poly_class = None
                if poly_results and poly_results[0].boxes:
                    poly_class = polythene_nonpoly_model.names[int(poly_results[0].boxes[0].cls[0])]

                # Save detection data to MongoDB
                detection_data = {
                    "camera": "camera1",
                    "object": object_name,
                   # "cover_status": cover_class if cover_class else "Non_cover",
                    "poly_status": poly_class if poly_class else "Non_poly",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                insert_detection_data(detections_collection_cam1, detection_data)

                # Draw bounding box and labels
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 2)
                cv2.putText(frame, f"{object_name} ({int(conf * 100)}%)", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        # Draw boundary curve
        frame = draw_curved_boundary(frame)

        # Encode frame as JPEG and yield for video stream
        _, jpeg = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

# Draw a curved boundary line for Camera 1
def draw_curved_boundary(frame):
    frame_height, frame_width = frame.shape[:2]
    curve_depth = 30
    curve_center_y = frame_height // 2

    num_points = frame_width
    curve_points = []

    for x in range(num_points):
        t = x / (frame_width - 1)
        y = curve_center_y + int(curve_depth * np.sin(np.pi * t))
        curve_points.append((x, y))

    for i in range(len(curve_points) - 1):
        cv2.line(frame, curve_points[i], curve_points[i + 1], (0, 255, 0), 2)

    return frame

# Process Camera 2 Feed
def process_camera2():
    global last_frame_time

    while True:
        current_time = time.time()
        if current_time - last_frame_time < 1 / fps_limit:
            time.sleep(0.01)
            continue

        frame = fetch_frame(camera=2)
        if frame is None:
            print("Failed to fetch frame from Camera 2.")
            time.sleep(0.5)
            continue

        # Detect bio or non-bio
        bio_nonBio_results = bio_nonBio_model.predict(source=frame, conf=0.5, show=False)
        for result in bio_nonBio_results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = box.conf[0].item()
                class_id = box.cls[0].item()

                if conf < 0.5:
                    continue

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

        # Encode frame as JPEG and yield for video stream
        _, jpeg = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
        
        '''----------------> Here the dry/wet model is running<-----------------
        # Detect dry or wet
        dry_wet_results = dry_wet_model.predict(source=frame, conf=0.5, show=False)
        for result in dry_wet_results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = box.conf[0].item()
                class_id = box.cls[0].item()

                if conf < 0.5:
                    continue

                object_name = dry_wet_model.names[int(class_id)]

                # Save detection data to MongoDB
                detection_data = {
                    "camera": "camera2",
                    "object": object_name,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                insert_detection_data(detections_collection_cam2, detection_data)

                # Draw bounding box and labels
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 2)
                cv2.putText(frame, f"{object_name} ({int(conf * 100)}%)", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)'''

        # Encode frame as JPEG and yield for video stream
        _, jpeg = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
