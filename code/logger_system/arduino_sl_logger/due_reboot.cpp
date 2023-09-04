#include "due_reboot.h"

void due_reboot(bool delay_reboot){
    // give time to print current information
    if (delay_reboot){
        delay(500);
    }

    REQUEST_EXTERNAL_RESET;
}
