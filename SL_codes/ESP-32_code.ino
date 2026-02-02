#include <Wire.h>
#include <MPU6050.h>

MPU6050 mpu;

// Updated flex sensor GPIOs: Thumb → Little Finger
const int flexPins[5] = {27, 32, 33, 34, 35};
int flexValues[5];

void setup() {
  // Initialize serial communication
  Serial.begin(115200);

  // Initialize I2C communication with updated pins
  Wire.begin(22, 21); // SDA → GPIO22, SCL → GPIO21

  // Initialize MPU6050
  mpu.initialize();
  if (mpu.testConnection()) {
    Serial.println("MPU6050 connected successfully");
  } else {
    Serial.println("MPU6050 connection failed");
  }

  // Set flex sensor pins as input
  for (int i = 0; i < 5; i++) {
    pinMode(flexPins[i], INPUT);
  }
}

void loop() {
  // Read all flex sensor values
  for (int i = 0; i < 5; i++) {
    flexValues[i] = analogRead(flexPins[i]);
  }

  // Read motion data from MPU6050
  int16_t ax, ay, az, gx, gy, gz;
  mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

  // Format and stream data via Serial
  for (int i = 0; i < 5; i++) {
    Serial.print(flexValues[i]);
    Serial.print(", ");
  }
  Serial.print(ax); Serial.print(", ");
  Serial.print(ay); Serial.print(", ");
  Serial.print(az); Serial.print(", ");
  Serial.print(gx); Serial.print(", ");
  Serial.print(gy); Serial.print(", ");
  Serial.println(gz);

  delay(100); // Stream at ~10Hz
}