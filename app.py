from flask import Flask, Response
import threading
from helper import process_camera1, process_camera2

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

@app.route('/camera1')
def camera1():
    return Response(gen_camera1(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/camera2')
def camera2():
    return Response(gen_camera2(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
