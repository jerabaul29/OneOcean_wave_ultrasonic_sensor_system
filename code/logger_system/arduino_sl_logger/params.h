#ifndef PARAMS_H
#define PARAMS_H

constexpr unsigned long baudrate {115200};

constexpr unsigned long millis_between_ADC_readings {100};
constexpr unsigned long millis_between_semaphores {100};

#define USE_VN_ON_DUE (1)
#define USE_DUMMY_VN_100 (0)

#if USE_DUMMY_VN_100 && USE_VN_ON_DUE
    #error "use either a true VN100, or a dummy VN100, not both"
#endif

#endif
