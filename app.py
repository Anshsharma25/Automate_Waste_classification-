from flask import Flask, Response, request, jsonify
from helper import (
    process_camera1, process_camera2, store_sensor_data, process_and_store_matching_data
)
import threading

app = Flask(__name__)

# Function to stream camera 1 feed
def gen_camera1():
    while True:
        frame = process_camera1()
        if frame is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

# Function to stream camera 2 feeds
def gen_camera2():
    while True:
        frame = process_camera2()
        if frame is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route("/sensor", methods=["POST"])
def sensor_data():
    data = request.get_json()
    if not data or 'distance' not in data or 'flag' not in data:
        return jsonify({"error": "Missing 'distance' or 'flag' field"}), 400
    
    # Process and store sensor data
    response_data, status_code = store_sensor_data(data)
    
    return jsonify(response_data), status_code

@app.route("/process_matching_data", methods=["GET"])
def process_matching_data():
    try:
        process_and_store_matching_data()
        return jsonify({"message": "Matching data processed and saved in final_match collection."}), 200
    except Exception as e:
        return jsonify({"error": "Error processing matching data", "message": str(e)}), 500

@app.route('/camera1')
def camera1():
    return Response(gen_camera1(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/camera2')
def camera2():
    return Response(gen_camera2(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
