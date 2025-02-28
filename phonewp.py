from pymongo import MongoClient
import random
from urllib.parse import quote_plus

# MongoDB Configuration
username = quote_plus("dustbin")  # Replace with your MongoDB username
password = quote_plus("Dustbin@123")  # Replace with your MongoDB password
MONGO_URI = f"mongodb+srv://{username}:{password}@cluster0.fmudd.mongodb.net/"
DATABASE_NAME = "garbage_detection"

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]

# Create and populate the phone_numbers collection
def create_phone_numbers_collection():
    phone_numbers_collection = db["phone_numbers"]
    phone_numbers_collection.delete_many({})  # Clear existing data
    
    phone_numbers = [
        {"phone_number": "919568286329", "active": True},
        {"phone_number": "918859826325", "active": True}
    ]
    
    phone_numbers_collection.insert_many(phone_numbers)
    print("Inserted phone numbers into the 'phone_numbers' collection.")

# Create and populate the dustbin_status_random collection
def create_dustbin_status_random_collection():
    dustbin_status_collection = db["dustbin_status_random"]
    dustbin_status_collection.delete_many({})  # Clear existing data
    
    # Generate 50 random documents with fill percentages for each dustbin
    dustbin_statuses = [
        {
            "A (Dry)": random.randint(20, 100),
            "B (Wet)": random.randint(20, 100),
            "C (Common)": random.randint(20, 100),
            "D (Liquid)": random.randint(20, 100)
        }
        for _ in range(50)
    ]
    
    dustbin_status_collection.insert_many(dustbin_statuses)
    print("Inserted random dustbin statuses into the 'dustbin_status_random' collection.")

# Main function to create collections and insert data
def main():
    print("Creating collections and inserting data...")
    create_phone_numbers_collection()
    create_dustbin_status_random_collection()
    print("Data insertion completed.")

if __name__ == "__main__":
    main()