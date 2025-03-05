import cv2
import serial
import time
import requests
import numpy as np
from ultralytics import YOLO

from exception import CustomException as e
from logger import logging

# Initialize YOLO Models
model_biogas = YOLO(r"models\biogas.pt")

logging.info("Model has been loaded.")

# Initialize Serial Communication with Arduino
arduino = serial.Serial(port="COM4", baudrate=9600, timeout=1)
time.sleep(2)
logging.info("Arduino connected.")

ESP8266_IP = "192.168.1.17"

class_to_flag = {
    'non-biodegradable': 1,
    'biodegradable': 2,
    'common': 3
}

region_pts = np.array([[150, 100], [100, 400], [450, 400], [450, 150]], np.int32)
region_pts = region_pts.reshape((-1, 1, 2))

def send_command(cmd):
    arduino.write(cmd.encode())
    time.sleep(1)
    response = arduino.readline().decode().strip()
    print(f"Arduino Response: {response}")
    logging.info(f"Command '{cmd}' sent to Arduino")

def send_flag(flag):
    url = f"http://{ESP8266_IP}/flag?value={flag}"
    try:
        response = requests.get(url, timeout=5)
        print(f"ESP8266 Response: {response.text}")
    except Exception as e:
        print(f"Error communicating with ESP8266: {e}")

def capture_frame(cam_url):
    cap = cv2.VideoCapture(cam_url)
    time.sleep(2)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        print("Failed to grab frame")
        return None
    cv2.imwrite("temp.jpg", frame)
    return frame

def detect_biodegradable(frame):
    results = model_biogas(frame)
    detected_classes = []
    region_count = 0
    
    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0])
            detected_class = model_biogas.names[class_id]
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2

            if cv2.pointPolygonTest(region_pts, (center_x, center_y), False) >= 0:
                detected_classes.append(detected_class)
                region_count += 1
    
    return detected_classes, region_count

def process_layer(cam_2):
    send_command("MOVE_FAST")  # Move plate quickly
    time.sleep(2)
    send_command("STOP")  # Stop plate

    frame = capture_frame(cam_2)
    if frame is None:
        return
    
    detected_classes, region_count = detect_biodegradable(frame)
    print(f"Objects detected: {region_count}")
    
    if region_count >= 2:
        bio_count = detected_classes.count("biodegradable")
        non_bio_count = detected_classes.count("non-biodegradable")
        
        if bio_count == 2:
            send_flag(class_to_flag['biodegradable'])
            send_command("THROW_BIO")
        elif non_bio_count == 2:
            send_flag(class_to_flag['non-biodegradable'])
            send_command("THROW_NON_BIO")
        else:
            send_command("MOVE_FAST")  # Move plate fast if mixed
    else:
        send_command("MOVE")  # Move to next rotation
    
    print("✅ Process Completed Successfully!")

cam_2 = "http://192.168.1.104/cam-hi.jpg"

if __name__ == "__main__":
    print("Starting Garbage Processing...")
    process_layer(cam_2)
