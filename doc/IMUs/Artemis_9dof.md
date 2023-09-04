To use the Artemis 9-dof extra IMUs, put together:

- Artemis Redboard
- Qwiic cable
- Adafruit ISM330DHCX + LIS3MDL FeatherWing - High Precision 9-DoF IMU

Program using:

https://github.com/jerabaul29/ultrasound_radar_bow_wave_sensor_Statsraad_Lehmkuhl_2021_2022/tree/main/code/logger_system/artemis_extra_imu

This should be compiled using the Sparkfun Artemis core v1.xx (NOT v2.xx). This relies on quite a few packets, including some that need to be changed from the default. In case of need, contact Jean Rabault.

*Specific note:*

In order to compile on Fabians laptop, this has been set up, see:

https://github.com/jerabaul29/ultrasound_radar_bow_wave_sensor_Statsraad_Lehmkuhl_2021_2022/issues/112
