from flask import Flask, Response
from helper import process_camera1, process_camera2

# Initialize Flask app
app = Flask(__name__)

# Video stream routes
@app.route('/camera1_feed')
def camera1_feed():
    """
    Route to serve the video feed from Camera 1.
    """
    return Response(
        process_camera1(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/camera2_feed')
def camera2_feed():
    """
    Route to serve the video feed from Camera 2.
    """
    return Response(
        process_camera2(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

