#include <Servo.h>

// Servo motors
Servo servoBase;
Servo servoElbow;

// Servo positions
int baseStart = 100;
int elbowStart = 180;
int baseTarget = 15;
int elbowTarget = -135;

// Motor driver pins (Net Motor)
int netMotor_IN1 = 7;
int netMotor_IN2 = 8;
int ena = 11;

// Motor Driver Pins (Flag-based Motor)
const int motorPin1 = 3;
const int motorPin2 = 4;
const int enablePin = 5;

int motorSpeed = 110;  // Motor speed

void setup() {
    Serial.begin(9600);
    Serial1.begin(9600); // For ESP8266 communication
    
    // Attach servos
    servoBase.attach(10);
    servoElbow.attach(9);
    
    // Set motor driver pins as OUTPUT
    pinMode(netMotor_IN1, OUTPUT);
    pinMode(netMotor_IN2, OUTPUT);
    pinMode(ena, OUTPUT);
    pinMode(motorPin1, OUTPUT);
    pinMode(motorPin2, OUTPUT);
    pinMode(enablePin, OUTPUT);
    
    // Enable motor driver
    digitalWrite(ena, HIGH);

    // Set servos to initial position
    servoBase.write(baseStart);
    servoElbow.write(elbowStart);
    
    Serial.println("🚀 System Ready. Waiting for commands...");
}

void moveServosSync(int baseAngle, int elbowAngle, int speed) {
    int basePos = servoBase.read();
    int elbowPos = servoElbow.read();
    
    while (basePos != baseAngle || elbowPos != elbowAngle) {
        if (basePos < baseAngle) basePos += speed;
        else if (basePos > baseAngle) basePos -= speed;
        
        if (elbowPos < elbowAngle) elbowPos += speed;
        else if (elbowPos > elbowAngle) elbowPos -= speed;
        
        basePos = constrain(basePos, min(basePos, baseAngle), max(basePos, baseAngle));
        elbowPos = constrain(elbowPos, min(elbowPos, elbowAngle), max(elbowPos, elbowAngle));
        
        servoBase.write(basePos);
        servoElbow.write(elbowPos);
        delay(10);
    }
}

void rotateNetFullSpeed() {
    Serial.println("Rotating plate at full speed for 4 seconds...");
    digitalWrite(netMotor_IN1, HIGH);
    digitalWrite(netMotor_IN2, LOW);
    delay(4000);
    digitalWrite(netMotor_IN1, LOW);
    digitalWrite(netMotor_IN2, LOW);
    Serial.println("Full speed rotation complete.");
}

void rotateNetHalfSpeed() {
    Serial.println("Rotating plate at 50% speed for 5 times...");
    for (int i = 0; i < 4; i++) {
        Serial.print("Rotation #");
        Serial.println(i + 1);

        analogWrite(ena, 60);
        digitalWrite(netMotor_IN1, HIGH);
        digitalWrite(netMotor_IN2, LOW);
        delay(380);

        digitalWrite(netMotor_IN1, LOW);
        digitalWrite(netMotor_IN2, LOW);
        delay(6000);
        
        
        Serial.println("Motion complete.");
    }
    analogWrite(ena, 255);
    Serial.println("50% speed rotations complete.");
}

void executeFlagAction(int flag) {
    if (flag == 5) {
        Serial.println("🏁 Executing Motion for Flag 5");

        
        // Step 1: Rotate Left
        rotateLeft(motorSpeed);
        delay(1100);
        stopMotor();

        // Step 2: Execute robotic hand servos
        delay(1000);
        Serial.println("🤖 Activating Robotic Hand...");
        moveServosSync(baseTarget, elbowTarget, 5);
        
        // Step 3: Return elbow
        delay(500);
        Serial.println("Returning elbow...");
        moveServosSync(baseTarget, elbowStart, 5);
        
        // Step 4: Return base
        Serial.println("Returning base...");
        moveServosSync(baseStart, elbowStart, 5);
        
        // Step 5: Wait for garbage to be dumped
        delay(1000);

        // Step 6: Rotate Right (Return to initial position)
        rotateRight(motorSpeed);
        delay(1200);
        stopMotor();

        
    }
    else if (flag == 4) {
        Serial.println("🏁 Executing Motion for Flag 4");

        // Step 1: Rotate Left
        rotateLeft(motorSpeed);
        delay(600);
        stopMotor();

        // Step 2: Execute robotic hand servos
        delay(1000);
        Serial.println("🤖 Activating Robotic Hand...");
        moveServosSync(baseTarget, elbowTarget, 5);
        
        // Step 3: Return elbow
        delay(500);
        Serial.println("Returning elbow...");
        moveServosSync(baseTarget, elbowStart, 5);
        
        // Step 4: Return base
        Serial.println("Returning base...");
        moveServosSync(baseStart, elbowStart, 5);

        // Step 5: Wait for garbage to be dumped
        delay(2000);

        rotateRight(motorSpeed);
        delay(600);
        stopMotor();

        
    } 
    else {
        Serial.println("⚠ Invalid flag received. Ignoring...");
    }
    
    delay(1000);  // Small delay before next check
}

void loop() {
    if (Serial.available()) {
        String command = Serial.readStringUntil('\n');
        command.trim();
        
        if (command == "MOVE") {
            Serial.println("Starting sequence...");
            
            // Step 1: Rotate Net at Full Speed
            rotateNetFullSpeed();
            
            // Step 2-5: Execute flag action and rotate net in sequence
            for (int i = 0; i < 4; i++) {
                int flag = receiveFlagFromSerial1();
                executeFlagAction(flag);
                rotateNetHalfSpeed();
            }
        }
    }
}

int receiveFlagFromSerial1() {
    while (!Serial1.available()) {
        // Wait until data is available
    }

    String receivedData = Serial1.readStringUntil('\n');
    receivedData.trim();
    
    Serial.print("📥 Raw Serial1 Data: ");
    Serial.println(receivedData);
    
    String flagStr = "";
    for (char c : receivedData) {
        if (isDigit(c)) {
            flagStr += c;
        }
    }
    
    if (flagStr.length() > 0) {
        int flag = flagStr.toInt();
        Serial.print("✅ Extracted Flag: ");
        Serial.println(flag);
        return flag;
    } else {
        Serial.println("⚠ No valid number found. Defaulting to flag 0.");
        return 0;  // Default flag
    }
}

void rotateRight(int speed) {
    Serial.println("🔄 Rotating Right");
    digitalWrite(motorPin1, HIGH);
    digitalWrite(motorPin2, LOW);
    analogWrite(enablePin, speed);
}

void rotateLeft(int speed) {
    Serial.println("🔄 Rotating Left");
    digitalWrite(motorPin1, LOW);
    digitalWrite(motorPin2, HIGH);
    analogWrite(enablePin, speed);
}

void stopMotor() {
    Serial.println("⏹ Motor Stopped");
    digitalWrite(motorPin1, LOW);
    digitalWrite(motorPin2, LOW);
    analogWrite(enablePin, 0);
}