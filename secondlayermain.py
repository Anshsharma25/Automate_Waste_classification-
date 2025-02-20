import cv2
import serial
import time
import requests
import numpy as np
from ultralytics import YOLO


MAX_HEIGHT=400
MAX_WIDTH=400
# --------------------------
# Setup: Load YOLO Model & Arduino Communication
# --------------------------
model = YOLO("biogas.pt")  # Load YOLO model

# Initialize serial communication with Arduino (update port if needed)
arduino = serial.Serial(port="COM4", baudrate=9600, timeout=1)
time.sleep(2)  # Allow Arduino to initialize

# ESP8266 IP Address (update as needed)
esp8266_ip = "192.168.1.20"

# Define angles for plate movement
rotation_angles = [0, 90, 180, 270]

# Mapping class names to flag values
class_to_flag = {
    'non-biodegradable': 1,
    'biodegradable': 2,
    'common': 3,
    'nonbiogasready': 5,
    'biogasready': 4
}

def send_command(cmd):
    """Send a command to Arduino and print its response."""
    arduino.write(f"{cmd}\n".encode())  # Ensure newline for Arduino parsing
    time.sleep(1)  # Allow time for Arduino to execute
    response = arduino.readline().decode().strip()
    print(f"🟢 Arduino Response: {response}")

def send_flag(flag):
    """Sends a flag value to ESP8266 via HTTP GET request."""
    url = f"http://{esp8266_ip}/flag?value={flag}"
    try:
        response = requests.get(url, timeout=5)
        print(f"🟢 ESP8266 Response: {response.text}")
    except Exception as e:
        print(f"❌ Error communicating with ESP8266: {e}")


import cv2
import time

def capture_image():
    """Capture a fresh image from ESP32-CAM and return the frame."""
    cam_url = 'http://192.168.1.104/cam-hi.jpg'  # Update with actual IP
    cap = cv2.VideoCapture(cam_url)
    
    time.sleep(1)  # Allow camera to adjust
    ret, frame = cap.read()
    cap.release()  # Ensure the camera is freed

    if not ret:
        print("❌ Error: Could not capture a fresh frame from the camera.")
        return None

    # Save the image with a unique timestamp to avoid overwriting
    timestamp = int(time.time())
    image_filename = f"captured_image_{timestamp}.jpg"
    cv2.imwrite(image_filename, frame)

    print(f"📸 New Image Captured: {image_filename}")
    return frame


# def capture_image():
#     """Capture an image from ESP32-CAM via HTTP request and return the frame."""
#     cam_url = 'http://192.168.1.104/cam-hi.jpg'  # ESP32-CAM URL
#     try:
#         response = requests.get(cam_url, timeout=5)
#         image_data = np.frombuffer(response.content, np.uint8)
#         frame = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
        
#         if frame is None:
#             print("❌ Error: Could not decode the image.")
#             return None

#         image_filename = "captured_image.jpg"
#         cv2.imwrite(image_filename, frame)
#         print(f"📸 Image captured and saved as '{image_filename}'.")
#         return frame

#     except Exception as e:
#         print(f"❌ Error capturing image: {e}")
#         return None

def detect_objects(frame):
    """Run YOLO detection and return detected class & confidence."""
    results = model(frame)
    detected_flags = []

    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0])
            confidence = box.conf[0].item()
            detected_class = model.names.get(class_id, "Unknown")  # Correct lookup
            
            # Get bounding box coordinates
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            width = x2 - x1
            height = y2 - y1

            # Ignore large objects (likely background)
            if width > MAX_WIDTH or height > MAX_HEIGHT:
                print(f"⚠ Ignoring {detected_class} (Too Large: {width}x{height})")
                continue  # Skip large detections

            # Normalize class name to lowercase (for matching)
            normalized_class = detected_class.lower().replace(" ", "-")

            # Draw detection box
            color = (0, 255, 0)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            label = f"{detected_class} {confidence:.2f}"
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            print(f"✅ Detected: {detected_class} | Confidence: {confidence:.2f}")



            if confidence > 0.4:
                flag = class_to_flag.get(detected_class.lower().replace(" ", "-"), None)
                if flag is not None:
                    detected_flags.append(flag)
    
    if detected_flags:
        selected_flag = min(detected_flags)
        send_flag(selected_flag)
        print(f"🟢 Sending Flag: {selected_flag}")
    else:
        print("⚠ No valid detections found.")

    return detected_flags

import time

# def main():
#     """Main loop to rotate net layer randomly, capture images, detect objects, and activate robotic hand."""
#     for _ in range(4):  # Repeat the process 4 times

#         print("\n✋ --- Activating Robotic Hand ---")
#         send_command("MOVE")
#         time.sleep(2)

#         # .
        
#         print("\n📸 --- Capturing Image for Object Detection ---")
#         frame = capture_image()
#         if frame is None:
#             continue

#         print("\n🔍 --- Running Object Detection ---")
#         detected_class = detect_objects(frame)  # Assuming this returns a class label
        
#         print("\n🤖 --- Rotating Third Layer Hand Motor Based on Detected Class ---")
#         send_command(f"HAND_MOTOR:{detected_class}")  # Adjust rotation accordingly
#         time.sleep(2)  

        

#         print("\n🔄 --- Returning Third Layer Hand Motor to Initial State ---")
#         send_command("HAND_MOTOR:RESET")
#         time.sleep(1)

#     print("✅ Process Completed Successfully!")


def main():
    """Main loop to rotate net layer randomly, capture images, detect objects, and activate robotic hand."""
    for _ in range(4):  # Repeat the process 4 times

        print("\n✋ --- Activating Robotic Hand ---")
        send_command("MOVE")
        time.sleep(1)

        print("\n📸 --- Capturing New Image for Object Detection ---")
        frame = capture_image()  # Fresh capture each time
        if frame is None:
            continue  # Skip this iteration if no image was captured

        print("\n🔍 --- Running Object Detection ---")
        detected_class = detect_objects(frame)  # Get new detection for the new frame

        print("\n🤖 --- Rotating Third Layer Hand Motor Based on Detected Class ---")
        send_command(f"HAND_MOTOR:{detected_class}")  # Adjust rotation accordingly
        time.sleep(2)  

        print("\n🔄 --- Returning Third Layer Hand Motor to Initial State ---")
        send_command("HAND_MOTOR:RESET")
        time.sleep(1)

    print("✅ Process Completed Successfully!")


if __name__ == "__main__":
    main()