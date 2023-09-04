// base the system on the Arduino Due for now (may be updated at a later point to some Artemis)
// TODO: extend size of all buffers by compiling through platformio
// TODO: replace the calls to Serial and Serial1 to ComputerSerial and VN100Serial or something similar
// TODO: add CRC on gauge data packet?
// TODO: on serial, put a "message semaphore" once in a while
// TODO: have some scripts monitoring that things run well

// a dummy VN100 string, for when not having a VN100 under the hand...
// \xfa\x14\x3e\x00\x3a\x00\x2f\x6b\xb3\xbd\x1d\xce\xa5\xbd\x2f\xcd\xd1\x3e\x40\x4b\x9a\xbf\x57\x4c\x18\xc0\xc8\x1f\x16\xc1\x1f\x80\xda\x37\x33\x9c\xac\xb8\xa8\x7f\x77\xbb\x67\xbf\x9d\x41\x1b\x2f\xcc\x42\x77\xe2\x07\x43\x9f\x1b\xe3\xc0\xcd\xee\x63\x41\x66\x62\x36\xbf\x92\x22\x27\xbf\x6e\xb9\x83\x3e\x6e\xd6\x30\x3f\x0e\x8f\x37\xbf\x60\x1a\xbf\x3d\xa3\x08\xfd\x3d\xbc\x0e\x7a\x3e\x04\x3a\x76\x3f\x6b\x4a\x84\x3e\x00\x56\x87\x38\x99\xee\xd3\x3e\x00\xe8\xc9\xba\x00\x32\xfb\xba\xcb\x12\x1c\xc1\x5f\x58\x0a

// packages of data are in the form:
// G[content]E\n for gauge reading
// I[content]E\n for IMU reading
// D [content]\n for debug messages
// W [content]\n for warnings
// S [content]\n for status

#include <Arduino.h>

#include "ram_info.h"

#include "params.h"
#include "due_reboot.h"
#include "expression_matcher.h"

// ------------------------------------------------------------------------------------------
// make sure we are using large enough serial buffers
static_assert(SERIAL_BUFFER_SIZE >= 1024, "set large enough serial buffers in $HOME/.arduino15/packages/arduino/hardware/sam/1.6.12/cores/arduino/RingBuffer.h");

// ------------------------------------------------------------------------------------------
// matcher stuff
bool match_res {false};

// to ask for a reboot, just send "BOOT" on serial
constexpr char boot_request[] {"BOOT"};
constexpr size_t boot_request_size = sizeof(boot_request)-1;
ExpressionMatcher matcher_boot {boot_request, boot_request_size};

// we need to be able to recognize VN100 headers; in hex: fa 14 3e 00 3a 00
// NOTE: may be a tiny bit different depending on end of line chars etc
constexpr char vn100_header[] {"\xfa\x14\x3e\x00\x3a\x00"};
constexpr size_t vn100_header_size = sizeof(vn100_header)-1;
ExpressionMatcher matcher_vn100_header {vn100_header, vn100_header_size};

// ------------------------------------------------------------------------------------------
// custom data structs for data transmission

// struct of ADC reading
struct ADC_Reading_Data {
    unsigned long reading_time;
    unsigned long reading_number;
    int value_channel_1;
    int value_channel_2;
    int value_channel_3;
} adc_reading_data;

// struct of VN100 message
constexpr size_t length_imu_data_frame {124};
size_t number_of_vn100_bytes_received {0};
struct IMU_Message {
    unsigned long receiving_time;
    unsigned long message_number;
    char message_data[length_imu_data_frame];
} imu_message;

// ------------------------------------------------------------------------------------------
// a dummy VN100 message for doing some testing
      constexpr char dummy_vn100_msg [length_imu_data_frame+1] {"\x2f\x6b\xb3\xbd\x1d\xce\xa5\xbd\x2f\xcd\xd1\x3e\x40\x4b\x9a\xbf\x57\x4c\x18\xc0\xc8\x1f\x16\xc1\x1f\x80\xda\x37\x33\x9c\xac\xb8\xa8\x7f\x77\xbb\x67\xbf\x9d\x41\x1b\x2f\xcc\x42\x77\xe2\x07\x43\x9f\x1b\xe3\xc0\xcd\xee\x63\x41\x66\x62\x36\xbf\x92\x22\x27\xbf\x6e\xb9\x83\x3e\x6e\xd6\x30\x3f\x0e\x8f\x37\xbf\x60\x1a\xbf\x3d\xa3\x08\xfd\x3d\xbc\x0e\x7a\x3e\x04\x3a\x76\x3f\x6b\x4a\x84\x3e\x00\x56\x87\x38\x99\xee\xd3\x3e\x00\xe8\xc9\xba\x00\x32\xfb\xba\xcb\x12\x1c\xc1\x5f\x58\xfa\x14\x3e\x00\x3a\x00"};

// ------------------------------------------------------------------------------------------
// timing

unsigned long time_last_ADC_readings {0};
unsigned long time_last_semaphore {0};

// ------------------------------------------------------------------------------------------
// helper functions

// use a custom boot message to make sure we can identify the board
void print_boot_message(void){
    Serial.println(F("S BOOT_ARD_DUE_SL_LOGGER"));  // a Status transmission
    delay(10);
}

void find_next_vn100_header(void){
    while (true){
        if (Serial1.available() > 0){
            unsigned char crrt_char = Serial1.read();
            if (matcher_vn100_header.match(crrt_char)){
                break;
            }
        }
    }
}

// ------------------------------------------------------------------------------------------
void setup(){
    delay(1000);

    // ------------------------------------------------------------
    // start serial, flush input buffer, and print boot message
    delay(10);
    Serial.begin(baudrate);
    delay(10);
    while (Serial.available() > 0){
        Serial.read();
    }
    print_boot_message();
    print_ram_info();

    // ------------------------------------------------------------
    // use the full ADC capability
    analogReadResolution(12);
    delay(10);

    // ------------------------------------------------------------
    // get ready to read messages from the VN100
    #if USE_VN_ON_DUE
        // start with correct baudrate
        Serial1.begin(57600);
        delay(5);

        // flush
        while (Serial1.available() > 0){
            Serial1.read();
        }

        Serial.println(F("S find first VN100 header..."));
        find_next_vn100_header();
    #endif

    // ------------------------------------------------------------
    // inits on the data structs
    adc_reading_data.reading_number = 0;
    imu_message.message_number = 0;

    // ------------------------------------------------------------
    // inits on timing
    time_last_ADC_readings = millis();
    time_last_semaphore = millis();

    // ------------------------------------------------------------
    Serial.println(F("S setup done"));
    Serial.print(F("S G struct has size: ")); Serial.println(sizeof(adc_reading_data));
    Serial.print(F("S I struct has size: ")); Serial.println(sizeof(imu_message));
}

// ------------------------------------------------------------------------------------------
void loop(){
    // ------------------------------------------------------------
    // check for requested reboot
    if (Serial.available() > 0){
        match_res = matcher_boot.match(Serial.read());

        if (match_res){
            Serial.println(F("S external boot request"));
            due_reboot();
            print_boot_message();
        }
    }

    // ------------------------------------------------------------
    // perform semaphore printing if needed
    if ((millis() - time_last_semaphore) >= millis_between_semaphores){
        time_last_semaphore += millis_between_semaphores;
        Serial.println(F("S SEMAPHORE"));
    }

    // ------------------------------------------------------------
    // perform ADC reading and transmit it if needed 
    if (millis() - time_last_ADC_readings >= millis_between_ADC_readings){
        time_last_ADC_readings += millis_between_ADC_readings;

        adc_reading_data.reading_time = millis();
        adc_reading_data.reading_number += 1;

        // note: need to put the right channels here, depending on which shield is being used
        adc_reading_data.value_channel_1 = analogRead(A0);
        adc_reading_data.value_channel_2 = analogRead(A2);
        adc_reading_data.value_channel_3 = analogRead(A4);

        Serial.print("G");  // a Gauges transmission
        Serial.write((uint8_t *)&adc_reading_data, sizeof(adc_reading_data));
        Serial.print("E\n");
    }

    // ------------------------------------------------------------
    // check if a VN100 IMU message has arrived, and, if so, put in struct and send
    #if USE_VN_ON_DUE
        if (Serial1.available() > 0){
            char crrt_vn_char = Serial1.read();

            // if ok to do so, put the char received in the struct message 
            // if not, it is time for a reset of this struct...
            if (number_of_vn100_bytes_received >= length_imu_data_frame){
                Serial.println(F("W hit max length VN100 buffer without finding header"));
                Serial.println(F("W find next vn100 header and resume..."));

                number_of_vn100_bytes_received = 0;

                // find the next VN100 header
                find_next_vn100_header();
            }
            else{
                imu_message.message_data[number_of_vn100_bytes_received] = crrt_vn_char;
                number_of_vn100_bytes_received++;
            }

            // if we have received a full message, put the metadata, send,
            // and reset current message length
            if (matcher_vn100_header.match(crrt_vn_char)){
                imu_message.receiving_time = millis();
                imu_message.message_number += 1;

                Serial.print("I");  // an Imu transmission
                Serial.write((uint8_t *)&imu_message, sizeof(imu_message));
                Serial.print("E\n");

                number_of_vn100_bytes_received = 0;
            }
        }
   #endif 

    #if USE_DUMMY_VN_100
        imu_message.receiving_time = millis();
        imu_message.message_number += 1;
        for (size_t ind=0; ind<length_imu_data_frame-1; ind++){
            imu_message.message_data[ind] = dummy_vn100_msg[ind];
        }
        Serial.print("I");  // an Imu transmission
        Serial.write((uint8_t *)&imu_message, sizeof(imu_message));
        Serial.print("E\n");
        delay(100);
    #endif
}
