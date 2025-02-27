#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>

const char* ssid = "Airtel_vish_0787";  // Replace with your WiFi SSID
const char* password = "air76152";  // Replace with your WiFi Password
const char* serverUrl = "http://192.168.1.14:5000/sensor_data";  // Replace with your API URL

WiFiClient client;
bool arduinoConnected = false;  // Track Arduino connection status
unsigned long lastReceivedTime = 0;  // Track last data received time

void setup() {
    Serial.begin(115200);
    WiFi.begin(ssid, password);

    Serial.print("Connecting to WiFi");
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.print(".");
    }
    Serial.println("\nWiFi Connected!");
}

void loop() {
    if (WiFi.status() == WL_CONNECTED) {
        if (Serial.available()) {
            String receivedData = Serial.readStringUntil('\n');  // Read full line
            receivedData.trim();  // Remove extra spaces

            if (receivedData.length() == 0) {
                Serial.println("⚠ Warning: Empty data received from Arduino!");
                return;
            }

            // Track last received time
            lastReceivedTime = millis();
            arduinoConnected = true;  // Set flag that Arduino is sending data

            Serial.println("✅ Data Received: " + receivedData);  // Debugging

            // Parse expected format: "Non-Biodegradable: X.XX% | Biodegradable: X.XX% | Common: X.XX% | Liquid: X.XX%"
            int nonBioIndex = receivedData.indexOf("Non-Biodegradable: ");
            int bioIndex = receivedData.indexOf("Biodegradable: ");
            int commonIndex = receivedData.indexOf("Common: ");
            int liquidIndex = receivedData.indexOf("Liquid: ");

            if (nonBioIndex != -1 && bioIndex != -1 && commonIndex != -1 && liquidIndex != -1) {
                float nonBio = receivedData.substring(nonBioIndex + 18, receivedData.indexOf("%", nonBioIndex)).toFloat();
                float bio = receivedData.substring(bioIndex + 14, receivedData.indexOf("%", bioIndex)).toFloat();
                float common = receivedData.substring(commonIndex + 8, receivedData.indexOf("%", commonIndex)).toFloat();
                float liquid = receivedData.substring(liquidIndex + 8, receivedData.indexOf("%", liquidIndex)).toFloat();

                // Ensure valid values
                if (nonBio < 0 || bio < 0 || common < 0 || liquid < 0) {
                    Serial.println("⚠ Warning: Invalid sensor values received!");
                    return;
                }

                HTTPClient http;
                http.begin(client, serverUrl);
                http.addHeader("Content-Type", "application/json");

                // Prepare JSON payload
                String jsonPayload = "{";
                jsonPayload += "\"non_biodegradable\":" + String(nonBio) + ",";
                jsonPayload += "\"biodegradable\":" + String(bio) + ",";
                jsonPayload += "\"common\":" + String(common) + ",";
                jsonPayload += "\"liquid\":" + String(liquid) + "}";

                Serial.println("📡 Sending JSON: " + jsonPayload);  // Debugging

                int httpResponseCode = http.POST(jsonPayload);

                // Print response from server
                Serial.print("🔄 HTTP Response Code: ");
                Serial.println(httpResponseCode);

                if (httpResponseCode > 0) {
                    String response = http.getString();
                    Serial.println("✅ Server Response: " + response);
                } else {
                    Serial.println("❌ Error in HTTP Request");
                }

                http.end();
            } else {
                Serial.println("❌ Parsing Failed! Invalid Data Format.");
            }
        }
    } else {
        Serial.println("❌ WiFi Not Connected!");
    }

    // Check if Arduino has stopped sending data
    if (arduinoConnected && millis() - lastReceivedTime > 5000) {
        Serial.println("⚠ Warning: No data received from Arduino for 5 seconds!");
        arduinoConnected = false;  // Reset flag
    }

    delay(1000);
}