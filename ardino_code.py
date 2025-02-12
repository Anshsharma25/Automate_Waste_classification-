import cv2
import serial
import time
from ultralytics import YOLO

# --------------------------
# Setup: Load YOLO Model & Arduino Communication
# --------------------------
model = YOLO("biogas.pt")  # Load your trained YOLO model

# Initialize serial communication with Arduino (update port if needed)
arduino = serial.Serial(port="COM11", baudrate=9600, timeout=1)
time.sleep(2)  # Allow time for Arduino to initialize

def send_command(cmd):
    """
    Send a command to Arduino and print its response.
    The command is encoded and sent over the serial connection.
    """
    arduino.write(cmd.encode())
    time.sleep(1)  # Give Arduino time to perform the action
    response = arduino.readline().decode().strip()
    print("Arduino Response:", response)

# --------------------------
# Step 1: Capture and Save Image
# --------------------------
# Replace the URL with your ESP32-CAM stream URL if different
cam_url = 'http://192.168.1.104/cam-hi.jpg'
cap = cv2.VideoCapture(cam_url)
ret, frame = cap.read()
cap.release()

if not ret:
    print("Error: Could not capture frame from camera.")
    exit()

# Save the captured image for record or further analysis
image_filename = "captured_image.jpg"
cv2.imwrite(image_filename, frame)
print(f"Image captured and saved as '{image_filename}'.")

# --------------------------
# Step 2: Run YOLO Object Detection and Draw Bounding Boxes
# --------------------------
results = model(frame)
object_detected = False  # Flag to check if any valid object is found

# Iterate through detections and draw bounding boxes
for result in results:
    for box in result.boxes:
        class_id = int(box.cls[0])
        confidence = box.conf[0].item()
        detected_class = model.names[class_id]
        # Retrieve bounding box coordinates
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        # Set box color (green for confident detections)
        color = (0, 255, 0)
        # Draw bounding box and label on the frame
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        label = f"{detected_class} {confidence:.2f}"
        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        print(f"Detected: {detected_class} | Confidence: {confidence:.2f}")
        # Use a confidence threshold to decide if detection is valid (adjust threshold as needed)
        if confidence > 0.5:
            object_detected = True

# Display the detection result with bounding boxes (optional)
cv2.imshow("Detections", frame)
cv2.waitKey(2000)  # Display for 2 seconds
cv2.destroyAllWindows()

# Save the final detection result with bounding boxes
result_filename = "detection_result.jpg"
cv2.imwrite(result_filename, frame)
print(f"Detection result saved as '{result_filename}'.")

# --------------------------
# Step 3: Activate Robotic Hand if Object is Detected
# --------------------------
if object_detected:
    print("Object detected. Activating robotic hand to push the object from the gate...")
    send_command("MOVE")  # Send command that matches the Arduino code's expectation
else:
    print("No object detected. Robotic hand will not be activated.")
