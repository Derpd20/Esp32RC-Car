#include <ESP8266WiFi.h>
#include <espnow.h>

void onReceive(uint8_t *mac, uint8_t *incomingData, uint8_t len) {
  const byte startByte = 0xFF;
  const byte endByte = '\n';

  // Sanity check: expect even-length packets (ID/value pairs)
  if (len % 2 != 0 || len == 0 || len > 60) {
    Serial.println("Invalid ESP-NOW packet length");
    return;
  }

  byte packet[64];
  packet[0] = startByte;
  packet[1] = len; // length of ID/value pairs
  memcpy(&packet[2], incomingData, len);
  packet[2 + len] = endByte;

  // Send framed packet over UART to Mega
  Serial.write(packet, len + 3); // 2 framing bytes + payload + end byte
}

void setup() {
  Serial.begin(9600);
  WiFi.mode(WIFI_STA);

  if (esp_now_init() != 0) {
    Serial.println("ESP-NOW init failed");
    return;
  }

  esp_now_set_self_role(ESP_NOW_ROLE_COMBO);
  esp_now_register_recv_cb(onReceive);
}

void loop() {
  // nothing needed here
}