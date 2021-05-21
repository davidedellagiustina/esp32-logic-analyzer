/*
 * Basically, we have here 3 processes running on the two different cores of the ESP32:
 *  - the first process is running on core 1 and it is responsible for collecting the data from a sensor connected to the probe pin;
 *  - the second process is running on core 0 and sends the bufferized data over the serial communication;
 *  - the third process is also running on core 0 and monitors and reports the buffer state.
 * Note that the entire program basically implements a classical producer-consumer algorithm.
 * Moreover, since sending raw data on the serial is so much slower than reading the probe pin value, we manage the buffer and therefore send the data over the serial encoding it with a run-length alorithm.
 */

// [ ===== SETTINGS ===== ]

const int probe = 23; // Probe pin (you should connect a proper pull-up/pull-down resistor there!)
const int serial_baudrate = 500000; // Don't go over 1MHz, otherwise you will read pretty much garbage
const int bufsize = 10000; // Size of the internal buffer (doesn't compile if too big)
const bool enable_bufmonitor = true; // Whether to enable the buffer-manager process
                                     // Disabling it will leave more CPU power for the serial-manager process
const int bufmonitor_interval = 1000; // Time interval (in milliseconds) when to check for buffer space

// [ ====== INTERNAL ===== ]

// Buffer
typedef struct { // Elements of the buffer, run-length encoding
  uint8_t elem;
  uint16_t count; // Max = 65535 (max_run)
} bufelem_t;
const int max_run = 65535;
bufelem_t buf[bufsize];
int cons_idx = 0; // Buffer index for the consumer (serial-manager process)
int prod_idx = 0; // Buffer index for the producer (data-collector process)
bufelem_t *prod_ptr; // Buffer pointer for the producer (for speeding it up)

// Processes
TaskHandle_t sermanager_handle, bufmanager_handle;

// [ ===== INIT ===== ]

// NOTE: setup and loop already run on core1 of the ESP32
// Therefore, we use the setup() method for making some general initialization, then use Both the setup and the loop for the data-collector process

// Main setup will initialize the process(es) for core 0
void setup() {

  // Enable serial communication here (will be used by both serial-manager and buffer-manager
  Serial.begin(serial_baudrate);
  
  // First disable the watchdog timer for core 0, otherwise it will reboot the ESP every 3/4 seconds
  disableCore0WDT();
  
  // Create the other task(s)
  // Args: code function, name, stack size (in words), input parameter, priority (the higher the better), handle, core number
  xTaskCreatePinnedToCore(sermanager, "serialManager", 10000, NULL, 1, &sermanager_handle, 0);
  if (enable_bufmonitor) xTaskCreatePinnedToCore(bufmanager, "bufferManager", 10000, NULL, 1, &bufmanager_handle, 0);

  // From now on, just care about core 1 tasks
  datacollect_setup();
  
}

// Basically, just callata collector loop
void loop() {
  datacollect_loop();
}
