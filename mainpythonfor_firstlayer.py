import cv2
import serial
import time
from ultralytics import YOLO  # Import YOLO from Ultralytics

# Load Custom YOLO Model
model = YOLO("poly_non_poly.pt")  # Load your trained YOLO model

# Initialize Serial Communication with Arduino
arduino = serial.Serial(port="COM4", baudrate=9600, timeout=1)  # Change COM8 if needed
time.sleep(2)  # Wait for connection

def send_command(cmd):
    """Send a command to Arduino and wait for response"""
    arduino.write(cmd.encode())  # Send command
    time.sleep(1)  # Wait for action to complete
    response = arduino.readline().decode().strip()  # Read response
    print(f"Arduino Response: {response}")

# Capture Image (Live Camera)
cap = cv2.VideoCapture("http://192.168.1.103/cam-hi.jpg")  # ESP32-CAM MJPEG stream URL

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    # Run YOLO detection on the captured frame
    results = model(frame)  # Run inference
    
    # Check for polythene detection
    polythene_detected = False
    for result in results:
        for box in result.boxes:  # Get bounding boxes
            class_id = int(box.cls[0])  # Class ID
            confidence = box.conf[0].item()  # Confidence score
            detected_class = model.names[class_id]  # Get class label

            print(f"Detected: {detected_class} (Confidence: {confidence:.2f})")

            if detected_class.lower() == "polythene":  # Match class name
                polythene_detected = True
                break

    # Decision Logic (Send Command to Arduino)
    if polythene_detected:
        print("Polythene detected! Activating cutter and hand pressure, then opening plate.")
        send_command('H')  # Hand Pressure
        send_command('C')  # Cutter
        send_command('O')  # Open Plate (DC Motor)
        send_command('init')
    else:
        print("Non-polythene detected! Opening plate only.")
        send_command('O')  # Open Plate (DC Motor)

    # Optional: Visualize the frame with bounding boxes for debugging
    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 2)
            label = model.names[int(box.cls[0])]
            cv2.putText(frame, f"{label} ({box.conf[0]:.2f})", 
                        (int(x1), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Display the frame with detections
    cv2.imshow("Detection", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()