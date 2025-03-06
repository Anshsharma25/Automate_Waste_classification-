#include <Servo.h>

// ---------------------
// Hardware Definitions
// ---------------------

// Hand Pressure Servo
Servo handPressure;
#define HAND_PRESSURE_PIN 6

// Cutter Motor
#define cutterMotorEnable 22
#define cutterMotorInput1 24
#define cutterMotorInput2 26

// Opening Plate Motor
#define openingPlateMotorEnable 32
#define openingPlateMotorInput1 28
#define openingPlateMotorInput2 30
#define ENCODER_A 2

// Servo Motors for Robotic Arm
Servo servoBase;
Servo servoElbow;

// Gate Servo (for flag handling)
Servo myServo;

// Initial and target angles for the arm servos
int baseStart = 80;
int elbowStart = 180;
int baseTarget = 0;
int elbowTarget = -135;

// Motor Driver for Net Motor (Plate Motor)
int netMotor_IN1 = 7;
int netMotor_IN2 = 8;
int ena = 11;

// Motor Driver for Flag Motor
const int motorPin1 = 3;
const int motorPin2 = 4;
const int enablePin = 5;

// Encoder Variables for Opening Plate Motor
volatile int encoderCount = 0;
int pulsesPerRotation = 100;
int targetRotations = 2;

// Motor Speed for Flag Motor
int motorSpeed = 110;

// ---------------------
// Interrupt Service Routine for Encoder
// ---------------------
void countPulses() {
    encoderCount++;
}

// ---------------------
// Setup Function
// ---------------------
void setup() {
    Serial.begin(9600);
    Serial1.begin(9600); // Used for ESP8266 communication (if available)

    // Attach Servos
    handPressure.attach(HAND_PRESSURE_PIN);
    handPressure.write(130);

    servoBase.attach(10);
    servoElbow.attach(9);
    servoBase.write(baseStart);
    servoElbow.write(elbowStart);

    // Gate servo (for flag-related actions)
    myServo.attach(52);
    myServo.write(0);  // Initialize servo to 0 degrees
    delay(1000);

    // Setup Cutter Motor Pins
    pinMode(cutterMotorEnable, OUTPUT);
    pinMode(cutterMotorInput1, OUTPUT);
    pinMode(cutterMotorInput2, OUTPUT);

    // Setup Opening Plate Motor Pins
    pinMode(openingPlateMotorEnable, OUTPUT);
    pinMode(openingPlateMotorInput1, OUTPUT);
    pinMode(openingPlateMotorInput2, OUTPUT);

    // Setup Net Motor (Plate Motor) Pins
    pinMode(netMotor_IN1, OUTPUT);
    pinMode(netMotor_IN2, OUTPUT);
    pinMode(ena, OUTPUT);
    analogWrite(ena, 255); // Full speed

    // Setup Flag Motor Pins
    pinMode(motorPin1, OUTPUT);
    pinMode(motorPin2, OUTPUT);
    pinMode(enablePin, OUTPUT);

    // Setup Encoder
    pinMode(ENCODER_A, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(ENCODER_A), countPulses, RISING);

    Serial.println("🚀 System Ready. Waiting for commands...");
}

// ---------------------
// Main Loop
// ---------------------
void loop() {
    if (Serial.available()) {
        String command = Serial.readStringUntil('\n');
        command.trim();

        if (command == "H") {
            activateHandPressure();
        }
        else if (command == "C") {
            activateCutter();
        }
        else if (command == "O") {
            // Rotate opening plate in one direction, then reverse after a delay.
            rotateOpeningPlate(true, 150);
            delay(2000);
            rotateOpeningPlate(false, 150);
        }
        else if (command == "MOVE") {
            Serial.println("Starting MOVE sequence...");
            rotateNetFullSpeed();
            for (int i = 0; i < 4; i++) {
                int flag = receiveFlagFromSerial1();
                // If no flag is received, use a default (3 = common/default)
                if (flag == 0) {
                    flag = 3;
                }
                executeFlagAction(flag);
                rotateNetHalfSpeed();
            }
        }
        else if (command == "STOP") {
            finalStopPlate();
            Serial.println("STOP command received. Plate movement disabled.");
        }
    }
}

// ---------------------
// Command Functions
// ---------------------

// Activate hand pressure by moving the hand pressure servo.
void activateHandPressure() {
    Serial.println("Hand Pressure Activated");
    handPressure.write(13);
    delay(500);
}

// Activate cutter motor: run cutter for 2 seconds then reset.
void activateCutter() {
    Serial.println("Cutter Motor Activated");
    digitalWrite(cutterMotorEnable, HIGH);
    digitalWrite(cutterMotorInput1, HIGH);
    digitalWrite(cutterMotorInput2, LOW);
    delay(2000);
    digitalWrite(cutterMotorEnable, LOW);
    handPressure.write(130);
    Serial.println("Cutter Motor Stopped");
}

// Rotate opening plate using encoder feedback with dynamic braking.
void rotateOpeningPlate(bool clockwise, int durationMs) {
    encoderCount = 0;
    int targetPulses = pulsesPerRotation * targetRotations;
    Serial.println(clockwise ? "Rotating Opening Plate Clockwise" : "Rotating Opening Plate Counterclockwise");

    // Start motor in desired direction
    digitalWrite(openingPlateMotorEnable, HIGH);
    digitalWrite(openingPlateMotorInput1, (clockwise ? HIGH : LOW));
    digitalWrite(openingPlateMotorInput2, (clockwise ? LOW : HIGH));

    unsigned long startTime = millis();
    while ((millis() - startTime) < durationMs && encoderCount < targetPulses) {
        // Waiting until either duration elapses or target pulses reached
    }

    // Stop the motor
    digitalWrite(openingPlateMotorEnable, LOW);
    // Dynamic braking: briefly reverse motor polarity
    digitalWrite(openingPlateMotorInput1, (clockwise ? LOW : HIGH));
    digitalWrite(openingPlateMotorInput2, (clockwise ? HIGH : LOW));
    delay(100); // Braking delay (adjust as needed)
    // Ensure all motor pins are LOW to fully stop the motor
    digitalWrite(openingPlateMotorInput1, LOW);
    digitalWrite(openingPlateMotorInput2, LOW);

    handPressure.write(130);
    Serial.println("Opening Plate Stopped");
}

// ---------------------
// Plate (Net Motor) Functions
// ---------------------

// Rotate plate at full speed for 2 seconds.
void rotateNetFullSpeed() {
    Serial.println("Rotating Plate at full speed...");
    digitalWrite(netMotor_IN1, HIGH);
    digitalWrite(netMotor_IN2, LOW);
    delay(2000);
    digitalWrite(netMotor_IN1, LOW);
    digitalWrite(netMotor_IN2, LOW);
}

// Rotate plate at half speed: run briefly then pause.
void rotateNetHalfSpeed() {
    Serial.println("Rotating Plate at 50% speed...");
    analogWrite(ena, 60); // Set motor to half speed
    digitalWrite(netMotor_IN1, HIGH);
    digitalWrite(netMotor_IN2, LOW);
    delay(400);
    digitalWrite(netMotor_IN1, LOW);
    digitalWrite(netMotor_IN2, LOW);
    delay(6000);
    analogWrite(ena, 255); // Restore full speed
}

// Final function to stop all plate movement completely.
void finalStopPlate() {
    // Stop net motor outputs
    digitalWrite(netMotor_IN1, LOW);
    digitalWrite(netMotor_IN2, LOW);
    analogWrite(ena, 0);
    // Ensure opening plate motor outputs are LOW
    digitalWrite(openingPlateMotorEnable, LOW);
    digitalWrite(openingPlateMotorInput1, LOW);
    digitalWrite(openingPlateMotorInput2, LOW);
}

// ---------------------
// ESP8266 Flag Reception
// ---------------------

// Try to receive a flag from Serial1 with a 2-second timeout.
int receiveFlagFromSerial1() {
    unsigned long startTime = millis();
    while (!Serial1.available() && (millis() - startTime < 2000)) {
        // Waiting for flag data from ESP8266
    }
    if (Serial1.available()) {
        String receivedData = Serial1.readStringUntil('\n');
        receivedData.trim();
        String flagStr = "";
        for (char c : receivedData) {
            if (isDigit(c))
                flagStr += c;
        }
        if (flagStr.length() > 0) {
            return flagStr.toInt();
        }
    }
    return 0; // No valid flag received
}

// ---------------------
// Flag Action Functions
// ---------------------

// Execute an action based on the received flag.
void executeFlagAction(int flag) {
    if (flag == 5) {  // e.g., nonbiogasready
        rotateLeft(motorSpeed);
        delay(1400);
        stopMotor();
        myServo.write(145); // Adjust servo to 145 degrees
        delay(500);
        moveServosSync(baseTarget, elbowTarget, 5);
        delay(500);
        moveServosSync(baseStart, elbowStart, 5);
        delay(500);
        myServo.write(10);  // Reset servo position
        rotateRight(motorSpeed);
        delay(1600);
        stopMotor();
    } else if (flag == 4) {  // e.g., biogasready
        rotateLeft(motorSpeed);
        delay(600);
        stopMotor();
        myServo.write(145);
        moveServosSync(baseTarget, elbowTarget, 5);
        delay(500);
        moveServosSync(baseStart, elbowStart, 5);
        delay(500);
        myServo.write(10);
        delay(500);
        rotateRight(motorSpeed);
        delay(700);
        stopMotor();
    } else if (flag == 3) {
        Serial.println("Default flag action (Common) executed.");
        // You can add default behavior here if desired.
    } else {
        Serial.print("Unknown flag received: ");
        Serial.println(flag);
    }
}

// Synchronized movement for the robotic arm servos.
void moveServosSync(int baseAngle, int elbowAngle, int speed) {
    servoBase.write(baseAngle);
    servoElbow.write(elbowAngle);
    delay(1000);
}

// ---------------------
// Flag Motor Control Functions
// ---------------------

void rotateRight(int speed) {
    digitalWrite(motorPin1, HIGH);
    digitalWrite(motorPin2, LOW);
    analogWrite(enablePin, speed);
}

void rotateLeft(int speed) {
    digitalWrite(motorPin1, LOW);
    digitalWrite(motorPin2, HIGH);
    analogWrite(enablePin, speed);
}

void stopMotor() {
    digitalWrite(motorPin1, LOW);
    digitalWrite(motorPin2, LOW);
    analogWrite(enablePin, 0);
}