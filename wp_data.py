# from flask import Flask, request, jsonify
# from pymongo import MongoClient
# from urllib.parse import quote_plus

# app = Flask(__name__)

# # MongoDB Setup
# username = quote_plus("dustbin")  # Replace with your MongoDB username
# password = quote_plus("Dustbin@123")  # Replace with your MongoDB password
# MONGO_URI = f"mongodb+srv://{username}:{password}@cluster0.fmudd.mongodb.net/"
# DATABASE_NAME = "garbage_detection"
# COLLECTION_NAME = "dustbin_status_random1"  # Collection name

# # Connect to MongoDB
# client = MongoClient(MONGO_URI)
# db = client[DATABASE_NAME]
# collection = db[COLLECTION_NAME]
# print("Connected to MongoDB. Collections:", db.list_collection_names())

# # --- Flask Route to Receive Sensor Data ---
# @app.route('/sensor_data', methods=['POST'])
# def receive_sensor_data():
#     try:
#         # Retrieve JSON data from the request
#         json_data = request.get_json(force=True)
#         print("Received JSON data:", json_data)

#         # Ensure missing values default to 0
#         default_values = {}
#         complete_data = {**default_values, **json_data}  # Merge default values with received data

#         # Insert the sensor data document into the collection
#         result = collection.insert_one(complete_data)
#         print("Inserted document with ID:", result.inserted_id)

#         # Remove the '_id' key before returning the response
#         complete_data.pop("_id", None)

#         return jsonify({
#             "message": "Sensor data inserted successfully.",
#             "data": complete_data,
#             "inserted_id": str(result.inserted_id)
#         }), 200

#     except Exception as e:
#         print("An error occurred:", e)
#         return jsonify({"error": str(e)}), 500

# # --- Main Execution ---
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000, debug=True)

from flask import Flask, request, jsonify
from pymongo import MongoClient
from urllib.parse import quote_plus

app = Flask(__name__)

# MongoDB Setup
username = quote_plus("dustbin")  # Replace with your MongoDB username
password = quote_plus("Dustbin@123")  # Replace with your MongoDB password
MONGO_URI = f"mongodb+srv://{username}:{password}@cluster0.fmudd.mongodb.net/"

# mongodb+srv://dustbin:<db_password>@cluster0.fmudd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
DATABASE_NAME = "garbage_detection"
COLLECTION_NAME = "dustbin_status_random1"  # Collection name

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]
print("Connected to MongoDB. Collections:", db.list_collection_names())

# --- Flask Route to Receive Sensor Data ---
@app.route('/sensor_data', methods=['POST'])
def receive_sensor_data():
    try:
        # Retrieve JSON data from the request
        json_data = request.get_json(force=True)
        print("Received JSON data:", json_data)

        # Ensure missing values default to 0
        default_values = {}
        complete_data = {**default_values, **json_data}  # Merge default values with received data

        # Insert the sensor data document into the collection
        result = collection.insert_one(complete_data)
        print("Inserted document with ID:", result.inserted_id)

        # Remove the '_id' key before returning the response
        complete_data.pop("_id", None)

        return jsonify({
            "message": "Sensor data inserted successfully.",
            "data": complete_data,
            "inserted_id": str(result.inserted_id)
        }), 200

    except Exception as e:
        print("An error occurred:", e)
        return jsonify({"error": str(e)}), 500

# --- Main Execution ---
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)