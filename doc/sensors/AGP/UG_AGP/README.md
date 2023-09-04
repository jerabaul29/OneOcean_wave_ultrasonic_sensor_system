A short Readme about the UG, model **IRU-3433-C60**.

# main sensors properties

- input: 24V
- output: 4-20mA
- range: 0.4m to 15m
- update rate / response time: 100ms minimum, i.e. 10 Hz max

# sensor programmation

- use the Thinkpad T490 "HYDROLAB-Len-Win-20_1
- use the I2000SWR_115 software (see icon on Desktop)
- the interface is "over power": use the UG probe, plug the UG in the sensor part of the APG USB interface, plug the 24V input in the 24V DC part of the APG USB interface, plug the APG USB interface to the laptop
- in the program, there are a number of parameters, see the https://www.apgsensors.com/reports/18-programmable-settings-you-need-in-an-ultrasonic-sensor website about the parameters
- the settings are written on non volatile memory
- settings suggestion:
  - units mm
  - blanking 1000 mm to avoid bad echos
  - sensitivity 75 (avoid echoes)
  - pulses 18
  - gain control 1 (autosense)
  - average 1 (we do the averaging ourselves)
  - window 15240 (no windowing)
  - out of range samples 0 (should not play a role)
  - sample rate 5 (5 is enough, and increases lifetime and reduces risk of echos)
  - multiplier: 1.0
  - offset: 0
  - temp comp: 1 (on)
  - max distance 15240 mm
  - noise threshold: 30
  - we do not change the calibration (see the 4 and 20 MA set point and calibrate). For reference:
    - IRU 3433 C60, part 124126-3007, serial AD9327
      - 4 MA set point: 305mm
      - 20 MA set point: 15240
      - 4 MA calibrate: 8200
      - 20 MA calibrate: 41000

# general shield properties

Simple ```U=RI``` measurement. Note: Mega is 0-5V, Due is 0-3.3V, Artemis is 0-3.3V but the ADC is only 0-2V. This leads to theoretical resistor values (take a bit higher for "safety"):

- 5.0V / 20mA = 250 Ohm
- 3.3V / 20mA = 165 Ohm
- 2.0V / 20mA = 100 Ohm

The measurement is a simple Ohm law circuit:

```
SENSOR_OUT ------------------------------------- ADC_XX
                           |
                           |
                          ---
                          | |
                          | | R = 180 Ohm: compatible with 3.3V board (arduino Due)
                          | |
                          ---
                           |
                           |
SENSOR_GND ------------------------------------ GND_ARDUINO
```

# individual shields

## S1

- Thought for Arduino Due (0-3.3V ADC range)
- R value: 180 theory, 179 measured; this is too high and will damage the Due actually, change to 160 Ohm; even this is too high, may need to consider that can get up to 22mA, maybe even up to 24mA.

# status

Tested from 0.4 to 15.2 meters (compared with laser range finder), works fine.

