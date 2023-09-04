#ifndef DUE_REBOOT_H
#define DUE_REBOOT_H

#include "Arduino.h"

// Defines so the device can do a self reset ------------------------------------
#define SYSRESETREQ    (1<<2)
#define VECTKEY        (0x05fa0000UL)
#define VECTKEY_MASK   (0x0000ffffUL)
#define AIRCR          (*(uint32_t*)0xe000ed0cUL) // fixed arch-defined address
#define REQUEST_EXTERNAL_RESET (AIRCR=(AIRCR&VECTKEY_MASK)|VECTKEY|SYSRESETREQ);

// perform a software reboot of the Arduino Due
void due_reboot(bool delay_reboot=true);

#endif
