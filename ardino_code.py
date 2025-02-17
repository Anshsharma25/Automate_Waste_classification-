import cv2
import serial
import time
import requests
from ultralytics import YOLO

# --------------------------
# Setup: Load YOLO Model & Arduino Communication
# --------------------------
model = YOLO("biogas.pt")  # Load YOLO model

# Initialize serial communication with Arduino (update port if needed)
arduino = serial.Serial(port="COM6", baudrate=9600, timeout=1)
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

def capture_image():
    """Capture an image from ESP32-CAM and return the frame."""
    cam_url = 'http://192.168.1.104/cam-hi.jpg'
    cap = cv2.VideoCapture(cam_url)
    time.sleep(1)  # Give time for the camera to adjust
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("❌ Error: Could not capture frame from camera.")
        return None

    image_filename = "captured_image.jpg"
    cv2.imwrite(image_filename, frame)
    print(f"📸 Image captured and saved as '{image_filename}'.")
    return frame

def detect_objects(frame):
    """Run YOLO detection and return detected class & confidence."""
    results = model(frame)
    detected_flags = []

    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0])
            confidence = box.conf[0].item()
            detected_class = model.names[class_id]
            if confidence > 0.5:
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

def main():
    """Main loop to rotate plate, capture images, detect objects, and activate robotic hand."""
    print("🔄 --- Rotating Plate at Full Speed for 4 Seconds ---")
    send_command("ROTATE_FULL_SPEED")
    time.sleep(4)
    send_command("STOP")
    time.sleep(5)

    for angle in rotation_angles:
        print(f"\n🔄 --- Moving Plate to {angle}° ---")
        send_command(f"ROTATE:{angle}")
        time.sleep(3)

        print("\n📸 --- Capturing Image ---")
        frame = capture_image()
        if frame is None:
            continue

        print("\n🔍 --- Running Object Detection ---")
        detect_objects(frame)

        print("\n🤖 --- Activating Robotic Hand ---")
        send_command("MOVE")
        time.sleep(3)
    
    print("✅ Process Completed Successfully!")

if __name__ == "__main__":
    main()