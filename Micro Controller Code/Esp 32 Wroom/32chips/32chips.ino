#include <WiFi.h>
#include <esp_now.h>

// ESP8266 MAC address
uint8_t peerMAC[] = { 0x48, 0x3F, 0xDA, 0x0C, 0x2D, 0x53 };

// Buffer
const int maxLen = 64;
byte serialBuffer[maxLen];
int bufferIndex = 0;

// Callback
void OnDataSent(const uint8_t *mac_addr, esp_now_send_status_t status) {
  char macStr[18];
  snprintf(macStr, sizeof(macStr), "%02X:%02X:%02X:%02X:%02X:%02X",
           mac_addr[0], mac_addr[1], mac_addr[2],
           mac_addr[3], mac_addr[4], mac_addr[5]);

  Serial.print("To ");
  Serial.print(macStr);
  Serial.print(" → ");
  Serial.println(status == ESP_NOW_SEND_SUCCESS ? "✅ SUCCESS" : "❌ FAIL");
}

void setup() {
  Serial.begin(115200);
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();

  if (esp_now_init() != ESP_OK) {
    Serial.println("❌ ESP-NOW init failed");
    while (true);
  }

  esp_now_register_send_cb(OnDataSent);

  esp_now_peer_info_t peerInfo = {};
  memcpy(peerInfo.peer_addr, peerMAC, 6);
  peerInfo.channel = 1;
  peerInfo.encrypt = false;

  if (esp_now_add_peer(&peerInfo) != ESP_OK) {
    Serial.println("❌ Failed to add peer");
    while (true);
  }

  Serial.println("✅ ESP32 serial bridge ready");
}

void loop() {
  while (Serial.available()) {
    byte incoming = Serial.read();

    if (bufferIndex < maxLen) {
      serialBuffer[bufferIndex++] = incoming;
    }

    // When full 3 control pairs received (ID+VAL x3 = 6 bytes)
    if (bufferIndex == 6) {
      esp_err_t result = esp_now_send(peerMAC, serialBuffer, bufferIndex);
      if (result != ESP_OK) {
        Serial.println("❌ Failed to send packet");
      }
      bufferIndex = 0;
    }
  }
}
