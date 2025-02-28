import logging
from bson.objectid import ObjectId  # For MongoDB ObjectId handling
import pymongo
import requests
from urllib.parse import quote_plus

# Configure Logging
LOG_FILE = "dustbin_monitoring.log"
logging.basicConfig(
    filename=LOG_FILE,
    filemode='a',  # Append mode
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# MongoDB Configuration
username = quote_plus("dustbin")  # Replace with your MongoDB username
password = quote_plus("Dustbin@123")  # Replace with your MongoDB password
MONGO_URI = f"mongodb+srv://{username}:{password}@cluster0.fmudd.mongodb.net/"
DB_NAME = "garbage_detection"
DUSTBIN_COLLECTION = "dustbin_status_random1"
PHONE_COLLECTION = "phone_numbers"

# WhatsApp API Configuration
ACCESS_TOKEN = 'EAAWmNYM0qV8BOZBkf0gLYEOvVT7qxMy3Okt26SdpxxClCTxxmiKN7yzPkIHwx6ZCsai8idh774NmJNYY6w6ms5FpLY5H3BmIq3HeDozbtY91vd9iWZBynKTh5AMBPUSonJcZCQdtcqwYgR6zpEZA3YTXb0aTKZAVziRGQvEsKukBKuYZCgO5lcQgg3Qc9Pd4q9EUgZDZD'
PHONE_NUMBER_ID = '426650087209143'
API_VERSION = 'v16.0'

# MongoDB Client
client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]
while True:
    def fetch_first_dustbin_status():
        """Fetch the first dustbin status (instead of a random one)."""
        try:
            result = db[DUSTBIN_COLLECTION].find_one({}, sort=[("_id", 1)])  # Pick the first document
            if result:
                logging.info("Dustbin status fetched successfully (First Entry).")
                return result
            logging.warning("No dustbin status found in the collection.")
            return None
        except Exception as err:
            logging.error(f"Error fetching first dustbin status: {err}")
            return None

    def fetch_all_registered_numbers():
        """Fetch all registered phone numbers."""
        try:
            results = db[PHONE_COLLECTION].find({"active": True}, {"phone_number": 1, "_id": 0})
            phone_numbers = [record["phone_number"] for record in results]
            logging.info(f"Fetched {len(phone_numbers)} registered phone numbers.")
            return phone_numbers
        except Exception as err:
            logging.error(f"Error fetching phone numbers: {err}")
            return []

    def send_whatsapp_message(phone_number_id, recipient_number, message_text):
        """Send a WhatsApp message to a recipient."""
        url = f"https://graph.facebook.com/{API_VERSION}/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_number,
            "type": "text",
            "text": {"body": message_text},
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            logging.info(f"Sending message to {recipient_number} - Payload: {payload}")
            response.raise_for_status()
            logging.info(f"Message sent successfully to {recipient_number}. Response: {response.json()}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to send message to {recipient_number}: {e}")

    def send_messages_to_all_registered_numbers(message_text):
        """Send messages to all registered phone numbers."""
        phone_numbers = fetch_all_registered_numbers()
        for phone_number in phone_numbers:
            send_whatsapp_message(PHONE_NUMBER_ID, phone_number, message_text)

    def monitor_dustbins(dustbin_status):
        """Monitor dustbin statuses and send alerts when necessary."""
        try:
            dustbin_status.pop("_id", None)  # Remove MongoDB ObjectId

            summary_message = "Dustbin Status Summary:\n"
            alert_messages = []

            for dustbin, fill_percentage in dustbin_status.items():
                if not isinstance(fill_percentage, (int, float)):
                    try:
                        fill_percentage = int(fill_percentage)
                    except ValueError:
                        logging.warning(f"Invalid fill percentage for dustbin '{dustbin}': {fill_percentage}")
                        continue

                adjusted_fill_percentage = (
                    fill_percentage + 5 if fill_percentage == 60 else
                    fill_percentage + 10 if fill_percentage == 70 else
                    fill_percentage
                )
                summary_message += f"{dustbin}: {adjusted_fill_percentage}% full\n"

                if adjusted_fill_percentage >= 65:
                    alert_messages.append(f"🚨 Alert: Dustbin '{dustbin}' is {adjusted_fill_percentage}% full. Please take action.")
                if adjusted_fill_percentage >= 80:
                    alert_messages.append(f"⚠ Critical Alert: Dustbin '{dustbin}' is {adjusted_fill_percentage}% full! Immediate action required!")

            consolidated_message = "\n".join(alert_messages) + "\n\n" + summary_message
            logging.info(f"Final Alert Message: {consolidated_message}")

            if alert_messages:  # Only send messages if there are alerts
                send_messages_to_all_registered_numbers(consolidated_message)
            else:
                logging.info("No dustbins exceeded the threshold. No messages sent.")

        except Exception as e:
            logging.error(f"Error in monitoring dustbins: {e}")

    def main():
        """Main function to execute the workflow."""
        logging.info("Starting dustbin monitoring script.")
        dustbin_status = fetch_first_dustbin_status()  # Pick first document
        if not dustbin_status:
            logging.warning("No dustbin status found. Exiting...")
            return
        monitor_dustbins(dustbin_status)
        logging.info("Dustbin monitoring completed.")

    if __name__ == "__main__":
        main()