#ifndef PARAMS_TRACKER
#define PARAMS_TRACKER

//--------------------------------------------------------------------------------
// IMU params
constexpr bool imu_use_magnetometer {false};
constexpr bool blink_when_use_IMU {true};

//--------------------------------------------------------------------------------
// wave data sampling and wave data processing parameters
// this is a bit of hard coding for now

// whether to use wave measurements mode at all or not
constexpr bool use_wave_measurements {true};

// we use FFT of length 2048; smaller is bad for frequency resolution
constexpr size_t fft_length {2048};

// the IMU is sampled at a rate of 10 Hz
// 20 minutes would be 20*60*10=12000 samples ie 5.85 non overlapping segments
// in practise, let's use 6 non overlapping segments then, i.e. 12288 samples (a bit over 20 minutes)
constexpr size_t total_number_of_samples {2048 * 6};

// use a 75% overlap in the Welch computation
constexpr size_t fft_overlap {512};

// how many segments does that give us in total?
// we want to cover 1228.8 seconds
// the first segment brings in (fft_length / sampling_freq), where sampling_freq is 10Hz (see the imu_manager), i.e. 204.8 seconds
// each subsequent segment brings in (fft_length / sampling_freq / 4) seconds, where 4 comes from 75% overlap, i.e. 51.2 seconds
// so we need a number of welch segments: (1 + (1228.8 - 204.8) / 51.2) = 21.0
constexpr size_t number_welch_segments {21};

// frequency resolution is identical for Welch and FFT
// = (sampling_freq_hz / fft_length)
constexpr float welch_frequency_resolution {10.0f / static_cast<float>(fft_length)};

constexpr size_t welch_bin_min {9};
constexpr size_t welch_bin_max {64};
constexpr size_t nbr_wave_packet_freqs = welch_bin_max - welch_bin_min;

constexpr size_t size_wave_packet_buffer {128};

// how often to take wave spectrum measurements
// this is a value in seconds, that:
// - should correspond to a GPS measurement
// - will indicate when the wave spectrum measurements are started
// for example:
// - if GPS measurements are performed each 30 minutes, then can take wave measurements each 30 minutes, or each hour, or each 2 hours, etc
// - to start each 2 hours, the value would be: 2 * 60 * 60
constexpr long interval_between_wave_spectra_measurements {2 * 60 * 60};
// tolerance in seconds for jitter; typically 5 minutes should be more than enough
constexpr long tolerance_seconds_start_wave_measurements {10 * 60};

// to test the welch processing code, we have the possibility ot use dummy IMU data:
constexpr bool use_dummy_imu_data {false};  // if true, use dummy IMU data
// the properties of the dummy signal that we generate; its form is "dummy_accel = amp * cos(frq * t) + DC"
// where amp = amp_eta * omega**2 with amp_eta the water elevation amplitude
constexpr float dummy_imu_elevation_amplitude = 1.0f;  // amp_eta, in meters
constexpr float dummy_imu_accel_frequency = 0.2266f;  // frq, in hz; this is "in the middle" of two frequency bins, convenient to check spectral energy leakage
// constexpr float dummy_imu_accel_frequency = 0.2246f;  // frq, in hz; this is "spot on" to one specific frequency bin
constexpr float pi = 3.14159265359f;
constexpr float sqrt2_f = 1.4142135623730951f;
constexpr float dummy_imu_accel_omega = 2.0f * pi * dummy_imu_accel_frequency;  // omega

constexpr float dummy_imu_accel_constant_component = 9.81f;  // DC
constexpr float dummy_imu_accel_amplitude = dummy_imu_elevation_amplitude * dummy_imu_accel_omega * dummy_imu_accel_omega;  // amp accel

constexpr bool use_hanning_window {true};
constexpr bool use_hamming_window {false};

static_assert(use_hanning_window, "use of hanning window is recommended; only override with a good reason!");
static_assert(!(use_hamming_window && use_hanning_window), "can only use one windowing at a time!");
static_assert((use_hamming_window || use_hanning_window), "we STRONGLY recommend to use windowing; otherwise, spectral leakage combined with acceleration spectrum scaling leads to SWH values that are off by up to 20 percents.");
static_assert(interval_between_wave_spectra_measurements % interval_between_gnss_measurements_seconds == 0, "should perform wave measurements at the same time as some GNSS fix acquisition");

//--------------------------------------------------------------------------------
// thermistor related parameters

constexpr bool use_thermistor_string {true};

// when to perform thermistors measurements; use the same convention as the other methods
constexpr long interval_between_thermistors_measurements_seconds = interval_between_gnss_measurements_seconds;  // thermistors measurements should be quite power efficient; do each time the GNSS position is taken
// tolerance in seconds for jitter on when to perform the thermistors measurement; typically 5 minutes should be more than enough
constexpr long tolerance_seconds_start_thermistors_measurements {5 * 60};

// how many thermistors to use on the thermistor string, at most
constexpr int number_of_thermistors {6};

// duration over which sample thermistor data
constexpr int duration_thermistor_acquisition_ms {60000};
// duration over which sample IMU data to get the attitude information
constexpr int duration_thermistor_imu_acquisition_ms {60000};
constexpr int number_of_thermistor_imu_measurements = duration_thermistor_imu_acquisition_ms / 100;

// max number of thermistor packets that we transmit in a single thermistors message
constexpr size_t max_nbr_thermistor_packets {8};

// min number of thermistors readings sent at once by defaul
constexpr size_t min_default_nbr_thermistor_packets {4};

// how many thermistor packets we keep in memory
constexpr size_t size_thermistors_packets_buffer {256};

// roll is -180 to 180; to map it to -128 to 127 maximum
constexpr float roll_float_to_int8_factor {0.7f};  // 180 * 0.7 = 126
// pitch is -90 to 90; to map it to -128 to 127 maximum
constexpr float pitch_float_to_int8_factor {1.4f};  // 90 * 1.4 = 126

static_assert(interval_between_thermistors_measurements_seconds % interval_between_gnss_measurements_seconds == 0, "should perform thermistors measurements at the same time as some GNSS fix acquisition");

//--------------------------------------------------------------------------------
// various minor params
// NOTE: would like a constexpr if better, but not supported yet it seems; 1 to blink, 0 to not blink
#define PERFORM_SLEEP_BLINK 1
constexpr unsigned long interval_between_sleep_LED_blink_seconds {120};
constexpr unsigned long duration_sleep_LED_blink_milliseconds {350};

//--------------------------------------------------------------------------------
void print_params(void);

#endif
