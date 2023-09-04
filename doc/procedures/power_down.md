To power down:

- switch off the RPi. For this:
  - connect to the RPi through SSH
  - issue a shutdown command: ```sudo shutdown now```
  - wait around 30 seconds, to let the time to the RPi to switch off gracefully (there is a bit of delay between asking for shutdown and the shutdown being fully performed)
  
- switch off power to the whole electronics box; for this, physically remove the 220V power input that comes out of the box from the 220V power socket.

- make sure that the 24V supply is discharged. The 24V power supply has quite big capacitors on its output, so, if there is no load (i.e., sensor) connected, it will be necessary to help it a bit to discharge. To make sure there is no power on the 24V rail:
  - open the logger box
    - if there are some instruments plugged in, these are taking power and will quickly discharge the 24V power supply capacitors
    - if there are no instruments plugged in, there is no power draw, and power on the 24V may remain for quite a long time. In this case:
      - plug in the male 1.5kOgm discharge plug (preferred method), *or* manually use the 1.5kOhm resistor to "short" the 24V output, by using it to short the black and red terminals on any of the 3 sensors white screw terminals
  - keep discharging until the blue LED of the 24V power adapter is completely switched off. To make sure it is completely empty, wait for around double the time it takes to switch off before stopping to discharge the 24V rail

**Never** perform any changes to the hardware (replace components, plug in or out sensors) without first powering down the whole system this way. **Never** plug in or out sensors without first making sure that the blue LED of the 24V power supply is completely switched off.
