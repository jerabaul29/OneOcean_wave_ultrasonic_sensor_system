// indication of good functioning:
// the "ON" LED is steady green to indicate that the board is powered
// the "TX" LED blinks fast to indicate data are transmitted over USB
// the blue "13" LED blinks steadily at 5Hz to indicate that the Kalman filter
// is running

#include "Arduino.h"

#include "imu_manager.h"
#include "watchdog_manager.h"

constexpr bool show_debug_output{false};
constexpr bool send_IMU_packets{true};
constexpr bool make_blink_in_use{true};

bool state_LED{false};
constexpr uint8_t PIN_LED{13};
constexpr unsigned int metadata{1};

struct IMUPacket {
  unsigned int millis_timestamp;
  float acc_N;
  float acc_E;
  float acc_D;
  float yaw__;
  float pitch;
  float roll_;
  unsigned int metadata;
} imu_packet;

void setup() {
  // --------------------------------------------------------------------------------
  // startup and configuration...
  delay(1000);

  // first set up the watchdog
  // WDT has 1 Hz frequency and raises interrupt after 32 ticks and resets after
  // 32 ticks, i.e. 32 seconds reset time.
  wdt.configure(WDT_1HZ, 32, 32);
  wdt.start();

  pinMode(PIN_LED, OUTPUT);

  // start of the serial
  Serial.begin(57600);
  delay(10);
  Serial.println(F("IMU_9dof_1"));

  Serial.print(F("sizeof imu_packet: "));
  Serial.println(sizeof(imu_packet));

  board_imu_manger.start_IMU();
}

void loop() {
  float acc_N;
  float acc_E;
  float acc_D;

  float yaw__;
  float pitch;
  float roll_;

  while (true) {
    digitalWrite(PIN_LED, state_LED);
    state_LED = !state_LED;

    wdt.restart();
    if (!board_imu_manger.get_new_reading(acc_N, acc_E, acc_D, yaw__, pitch,
                                          roll_)) {
      Serial.println(F("ERROR gather_imu_data"));
      Serial.println(F("ERROR reboot"));
      while (true) {
      };
    }

    if (isnan(acc_N) || isnan(acc_E) || isnan(acc_D) || isnan(yaw__) || isnan(pitch) || isnan(roll_)){
      Serial.print(F("ERROR obtained nan"));
      Serial.println(F("ERROR reboot"));
      while (true){
      }
    }

    if (show_debug_output) {
      Serial.print(F("DEBUG_OUT | ms "));
      Serial.print(millis());
      Serial.print(F(" | acc_D "));
      Serial.print(acc_D);
      Serial.print(F(" | acc_E "));
      Serial.print(acc_E);
      Serial.print(F(" | acc_N "));
      Serial.print(acc_N);
      Serial.print(F(" | yaw__ "));
      Serial.print(yaw__);
      Serial.print(F(" | pitch "));
      Serial.print(pitch);
      Serial.print(F(" | roll_ "));
      Serial.print(roll_);
      Serial.println();
    }

    if (send_IMU_packets) {
      imu_packet.millis_timestamp = millis();
      imu_packet.acc_N = acc_N;
      imu_packet.acc_E = acc_E;
      imu_packet.acc_D = acc_D;
      imu_packet.yaw__ = yaw__;
      imu_packet.pitch = pitch;
      imu_packet.roll_ = roll_;
      imu_packet.metadata = metadata;

      Serial.println(F("SEMAPHORE_EXTRA_IMU"));
      Serial.write((uint8_t *)&imu_packet, sizeof(imu_packet));
      Serial.println();
    }
  }
}
