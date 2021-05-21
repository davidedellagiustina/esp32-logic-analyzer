/*
 * Buffer manager process, running on core 0.
 */

// This function should never return (therefore the endless loop)
void bufmanager(void *params) {
  bufmanager_setup();
  for(;;) { bufmanager_loop(); }
}

void bufmanager_setup() {}

void bufmanager_loop() {
  int free_buf_space = (bufsize + cons_idx - prod_idx - 1) % bufsize;
  Serial.print("INFO::FREEBUF=" + String(free_buf_space) + "\n");  // Must be oneline for avoiding interleaving problems
  delay(bufmonitor_interval);
}
