/*
 * Serial manager process, running on core 0.
 */

// This function should never return (therefore the endless loop)
void sermanager(void *params) {
  sermanager_setup();
  for(;;) { sermanager_loop(); }
}

void sermanager_setup() {}

void sermanager_loop() {
  if (cons_idx != prod_idx) {
    Serial.print("DATA::" + String(buf[cons_idx].elem) + "x" + String(buf[cons_idx].t_start) + "-" + String(buf[cons_idx].t_end) + "\n"); // Must be oneline for avoiding interleaving problems
    cons_idx = (cons_idx + 1) % bufsize;
  }
}
