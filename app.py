from flask import Flask, Response , request,jsonify ,make_response
import threading
from helper import process_camera1, process_camera2 ,process_ultrasonic_data
import json

app = Flask(__name__)

# Function to stream camera 1 feed
def gen_camera1():
    while True:
        frame = process_camera1()
        if frame is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

# Function to stream camera 2 feed
def gen_camera2():
    while True:
        frame = process_camera2()
        if frame is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
            


@app.route('/ultrasonic', methods=['POST'])
def ultrasonic():
    data = request.get_json()
    if not data or 'timestamp' not in data or 'flag' not in data:
        return jsonify({"error": "Missing 'timestamp' or 'flag' field"}), 400

    timestamp = data['timestamp']
    flag = data['flag']

    # Process the data (e.g., store in a database)
    # For demonstration, we'll just print it
    print(f"Received data: Timestamp = {timestamp}, Flag = {flag}")

    return jsonify({"message": "Data received successfully"}), 200

@app.route('/camera1')
def camera1():
    return Response(gen_camera1(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/camera2')
def camera2():
    return Response(gen_camera2(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
