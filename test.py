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
arduino = serial.Serial(port="COM10", baudrate=9600, timeout=1)
time.sleep(2)  # Allow Arduino to initialize

# ESP8266 IP Address (update as needed)
esp8266_ip = "192.168.1.19"

# Mapping class names to flag values
class_to_flag = {
    'non-biodegradable': 1,
    'biodegradable': 2,
    'common': 3,
    'nonbiogasready': 5,
    'biogasready': 4  # Added flag for 'biogasready'
}

# Define bounding box size thresholds (Adjust as needed)
MAX_WIDTH = 500  # Ignore objects wider than this
MAX_HEIGHT = 500  # Ignore objects taller than this

# Define class-specific bounding box colors (BGR format)
class_colors = {
    'non-biodegradable': (0, 0, 255),  # Red
    'biodegradable': (0, 255, 0),  # Green
    'common': (255, 0, 0),  # Blue
    'nonbiogasready': (255, 255, 0),  # Cyan
    'biogasready': (128, 0, 128)  # Purple
}

def send_command(cmd):
    """Send a command to Arduino and print its response."""
    arduino.write(f"{cmd}\n".encode())  # Ensure newline for Arduino parsing
    time.sleep(1)  # Allow time for Arduino to execute
    response = arduino.readline().decode().strip()
    print(f"🟢 Arduino Response: {response}")

def send_flag(flag):
    """Send a flag value to ESP8266 via HTTP GET request."""
    url = f"http://{esp8266_ip}/flag?value={flag}"
    try:
        response = requests.get(url, timeout=5)
        print(f"🟢 ESP8266 Response: {response.text}")
    except Exception as e:
        print(f"❌ Error communicating with ESP8266: {e}")

def capture_image():
    """Capture an image from ESP32-CAM and return the frame."""
    cam_url = 'http://192.168.1.104/cam-hi.jpg'  # Update with your ESP32 IP
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
    """Run YOLO detection on the frame and filter out large objects."""
    results = model(frame)
    valid_flags = []  # Stores flags of detected objects that are NOT ignored

    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0])
            confidence = box.conf[0].item()
            detected_class = model.names[class_id]

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

            # Get bounding box color for the detected class (default to white if not found)
            color = class_colors.get(normalized_class, (255, 255, 255))

            # Draw detection box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            label = f"{detected_class} {confidence:.2f}"
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            print(f"✅ Detected: {detected_class} | Confidence: {confidence:.2f}")

            if confidence > 0.25:  # Only consider objects with > 25% confidence
                flag = class_to_flag.get(normalized_class, None)
                if flag is not None:
                    valid_flags.append(flag)  # Add only valid (non-ignored) flags

    result_filename = "detection_result.jpg"
    cv2.imwrite(result_filename, frame)
    print(f"📂 Detection result saved as '{result_filename}'.")

    # Send the flag ONLY IF there are valid detections
    if valid_flags:
        selected_flag = min(valid_flags)  # Pick the smallest valid flag (or change logic as needed)
        send_flag(selected_flag)
        print(f"🟢 Sending Flag: {selected_flag}")
    else:
        print("⚠ No valid detections found after filtering large objects.")

    return valid_flags

def main():
    """Main loop to rotate plate, capture images, run object detection, and activate robotic hand."""
    for rotation in range(4):  # Rotate plate 4 times
        for angle in [0, 90]:  # Rotate between 0° and 90°
            print(f"\n🔄 --- Moving Plate to {angle}° ---")
            send_command(f"ROTATE:{angle}")  # Command to rotate plate
            time.sleep(2)  # Wait for plate to move

            print("\n📸 --- Capturing Image ---")
            frame = capture_image()
            if frame is None:
                continue  # Skip to next iteration if image capture fails

            print("\n🔍 --- Running Object Detection ---")
            detected_objects = detect_objects(frame)

            if detected_objects:
                print("\n🤖 --- Activating Robotic Hand ---")
                send_command("MOVE")  # Trigger robotic hand
                time.sleep(3)  # Allow time for hand movement

        # After every 4th rotation, send the flag for that position
        print(f"\n📸 --- Capturing Image and Sending Flag for Rotation {rotation + 1} ---")
        send_flag(rotation + 1)
        time.sleep(2)  # Delay between rotations for stability

    print("✅ Process Completed Successfully!")

if __name__ == "__main__":
    main()