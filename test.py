from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
from urllib.parse import quote_plus

app = Flask(__name__)

# MongoDB Setup
username = quote_plus("dustbin")  # Replace with your MongoDB username
password = quote_plus("Dustbin@123")  # Replace with your MongoDB password
MONGO_URI = f"mongodb+srv://{username}:{password}@cluster0.fmudd.mongodb.net/"
DATABASE_NAME = "Detection"

# Connect to MongoDB
try:
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client[DATABASE_NAME]
    sensor_collection = db["sensor_data"]
    sensor_collection.create_index("timestamp", expireAfterSeconds=7200)
    print("Connected to MongoDB successfully.")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    exit()

@app.route("/sensor", methods=["POST"])
def sensor_data():
    data = request.get_json()
    print(f"Received data: {data}")  # Debugging line
    
    # Ensure required fields are present
    required_fields = ["distance", "flag"]
    
    if not data:
        return jsonify({"error": "No JSON data received"}), 400
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields", "received": data}), 400

    # Validate distance and flag
    try:
        distance = float(data['distance'])
    except ValueError:
        return jsonify({"error": "Invalid distance value. It must be a number."}), 400
    
    flag = int(data['flag'])
    
    # Determine object detection status based on flag
    if flag == 1:
        detection_status = "Object detected"
    else:
        detection_status = "No object detected"

    # Generate a timestamp (you can also pass it from the Arduino if needed)
    timestamp = datetime.now()

    # Prepare sensor entry for MongoDB
    sensor_entry = {
        "timestamp": timestamp,
        "distance": distance,
        "flag": flag,
        "detection_status": detection_status
    }
    
    # Save data to MongoDB
    try:
        sensor_collection.insert_one(sensor_entry)
        print("Data saved to MongoDB (sensor_data).")
    except Exception as e:
        print(f"Error saving data to MongoDB: {e}")
        return jsonify({"error": "Error saving data to MongoDB"}), 500
    
    return jsonify({
        "message": "Data received successfully",
        "distance": distance,
        "flag": flag,
        "detection_status": detection_status
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
