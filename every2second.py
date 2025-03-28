# import cv2
# import torch
# import time
# from ultralytics import YOLO
# import requests
# import numpy as np

# # Load YOLO model
# model = YOLO("biogas.pt")  # Change to your custom model if needed

# # Camera URL
# camera_url = "http://192.168.1.104/cam-hi.jpg"

# try:
#     while True:
#         start_time = time.time()
        
#         # Capture frame from external camera
#         response = requests.get(camera_url)
#         if response.status_code == 200:
#             img_arr = np.array(bytearray(response.content), dtype=np.uint8)
#             frame = cv2.imdecode(img_arr, -1)
#         else:
#             print("Failed to retrieve image from camera")
#             continue
        
#         # Perform object detection
#         results = model(frame)
        
#         # Draw bounding boxes
#         for result in results:
#             for box in result.boxes:
#                 x1, y1, x2, y2 = map(int, box.xyxy[0])  # Bounding box coordinates
#                 conf = float(box.conf[0])  # Confidence score
#                 cls = int(box.cls[0])  # Class ID
#                 label = f"{model.names[cls]}: {conf:.2f}"
                
#                 # Draw rectangle and label
#                 cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
#                 cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
#         # Display result
#         cv2.imshow("Object Detection", frame)
        
#         # Wait for 2 seconds
#         while time.time() - start_time < 2:
#             pass
        
#         # Press 'q' to quit
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break

# finally:
#     cv2.destroyAllWindows()



import cv2
import torch
import time
import logging
from ultralytics import YOLO
import requests
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load YOLO model
model = YOLO("biogas.pt")  # Change to your custom model if needed

# Camera URL
camera_url = "http://192.168.1.104/cam-hi.jpg"

# Define region of interest (ROI)
region_pts = np.array([
    [219, 146], 
    [185, 224], 
    [174, 294], 
    [173, 365], 
    [368, 437], 
    [403, 139], 
    [224, 145]
], np.int32)
region_pts = region_pts.reshape((-1, 1, 2))

# Define bounding box size limits
MAX_WIDTH = 400
MAX_HEIGHT = 400

try:
    while True:
        start_time = time.time()
        
        # Capture frame from external camera
        response = requests.get(camera_url)
        if response.status_code == 200:
            img_arr = np.array(bytearray(response.content), dtype=np.uint8)
            frame = cv2.imdecode(img_arr, -1)
        else:
            logging.error("Failed to retrieve image from camera")
            continue

        # Perform object detection
        results = model(frame)

        # Draw region of interest
        cv2.polylines(frame, [region_pts], isClosed=True, color=(0, 0, 255), thickness=2)

        # Process detections
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])  # Bounding box coordinates
                conf = float(box.conf[0])  # Confidence score
                cls = int(box.cls[0])  # Class ID
                label = f"{model.names[cls]}: {conf:.2f}"

                # Compute bounding box size
                box_width = x2 - x1
                box_height = y2 - y1

                # Ignore large bounding boxes
                if box_width * box_height > MAX_HEIGHT * MAX_WIDTH:
                    logging.info(f"Ignored large bounding box: {(x1, y1, x2, y2)}")
                    continue

                # Compute center of bounding box
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                center_point = (center_x, center_y)

                # Check if the center of the box is inside the ROI
                if cv2.pointPolygonTest(region_pts, center_point, False) >= 0:
                    # Draw bounding box and label only if inside ROI
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Display result
        cv2.imshow("Object Detection", frame)

        # Maintain 2-second delay
        while time.time() - start_time < 2:
            pass

        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    cv2.destroyAllWindows()
