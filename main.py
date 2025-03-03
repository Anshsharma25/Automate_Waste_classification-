import cv2
import serial
import time
import requests
import numpy as np
from ultralytics import YOLO

from exception import CustomException as e
from logger import logging

MAX_HEIGHT = 400
MAX_WIDTH = 400

RED_BOX_X1, RED_BOX_Y1 = 150, 200
RED_BOX_X2, RED_BOX_Y2 = 400, 300

model_poly = YOLO(r"models\poly_non_poly.pt")
model_biogas = YOLO(r"models\biogas.pt")

logging.info("Models have been loaded.")

arduino = serial.Serial(port="COM3", baudrate=9600, timeout=1)  
time.sleep(2)

logging.info("Arduino connected.")

ESP8266_IP = "192.168.1.17"

class_to_flag = {
    'non-biodegradable': 1,
    'biodegradable': 2,
    'common': 3,
    'nonbiogasready': 5,
    'biogasready': 4
}

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
        logging.info(f"Response '{response.text}' sent.")
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
    
    image_path = "temp.jpg"
    cv2.imwrite(image_path, frame)
    logging.info(f"Camera shot '{cam_url}' captured successfully.")
    return frame

def detect_polythene(image_path):
    results = model_poly(image_path)
    
    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0])
            detected_class = model_poly.names[class_id]
            logging.info(f"Class detected: {detected_class}")
            print(f"Detected: {detected_class}")
            if detected_class.lower() == "polythene":
                return True
    return False

def process_first_layer(cam_1):
    frame = capture_frame(cam_1)
    if frame is None:
        return
    
    polythene_detected = detect_polythene("temp.jpg")
    
    if polythene_detected:
        send_command('H')
        time.sleep(0.5)
        send_command('C')
        time.sleep(0.5)
    send_command('O')

def detect_biodegradable_in_redbox(image_path):
    frame = cv2.imread(image_path)
    results = model_biogas(image_path)
    detected_flags = []
    detected_in_red_box = False
    cv2.rectangle(frame, (RED_BOX_X1, RED_BOX_Y1), (RED_BOX_X2, RED_BOX_Y2), (0, 0, 255), 3)
    
    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            class_id = int(box.cls[0])
            detected_class = model_biogas.names[class_id]
            box_area = (x2 - x1) * (y2 - y1)
            
            if box_area > 50000:  # Ignore large bounding boxes
                continue
            
            if not (x2 < RED_BOX_X1 or x1 > RED_BOX_X2 or y2 < RED_BOX_Y1 or y1 > RED_BOX_Y2):
                detected_in_red_box = True
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                cv2.putText(frame, detected_class, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                normalized_class = detected_class.lower().replace(" ", "-")
                flag = class_to_flag.get(normalized_class, None)
                if flag is not None:
                    detected_flags.append(flag)
    
    cv2.imwrite("temp.jpg", frame)
    
    if detected_flags:
        selected_flag = min(detected_flags)
        send_flag(selected_flag)
        return True
    return False

def process_second_third_layer(cam_2):
    detected = False
    for _ in range(4):
        send_command("MOVE")
        time.sleep(1)
        frame = capture_frame(cam_2)
        if frame is None:
            continue
        detected = detect_biodegradable_in_redbox("temp.jpg")
        if detected:
            break
    if not detected:
        send_command("MOVE")
    send_command("HAND_MOTOR:RESET")

def run_full_process():
    cam_1 = "http://192.168.1.103/cam-hi.jpg"
    cam_2 = "http://192.168.1.104/cam-hi.jpg"
    
    for i in range(4):
        print(f"Starting Cycle {i+1}...")
        process_first_layer(cam_1)
        time.sleep(2)
        process_second_third_layer(cam_2)
    print("✅ All 4 Cycles Completed Successfully!")

if _name_ == "_main_":
    run_full_process()