// Bench image: shows the 8 inputs live and switches the relays, to check the wiring before the press firmware runs.
//   A, B, C toggle relays 1, 2, 3. Hold A and C together to switch all relays off. Every relay switches off by itself
//   after 10 s, and while input 3 or 4 is off. Build and flash: pio run -e bench -t upload
#include <M5StamPLC.h>

#include "relays.h"

constexpr uint8_t IN_ESTOP_OK = 2, IN_PRESSURE_OK = 3;   // inputs 3 and 4, as in src/main.cpp

static bench::Relays relays;

void setup() {
    M5StamPLC.begin();
    Serial.begin(115200);
    M5StamPLC.writePlcAllRelay(0);
}

void loop() {
    M5StamPLC.update();
    const bool toggle[4] = {M5StamPLC.BtnA().wasPressed(), M5StamPLC.BtnB().wasPressed(), M5StamPLC.BtnC().wasPressed(),
                            false};
    relays.step(toggle, M5StamPLC.BtnA().isPressed() && M5StamPLC.BtnC().isPressed(),
                M5StamPLC.readPlcInput(IN_ESTOP_OK) && M5StamPLC.readPlcInput(IN_PRESSURE_OK), millis());
    for (uint8_t i = 0; i < 4; ++i) {
        if (M5StamPLC.readPlcRelay(i) != relays.on[i]) M5StamPLC.writePlcRelay(i, relays.on[i]);
    }

    static uint32_t last = 0;
    if (millis() - last < 200) return;
    last = millis();
    auto& d = M5StamPLC.Display();
    d.fillScreen(TFT_BLACK);
    d.setTextSize(2);
    d.setTextColor(TFT_YELLOW);
    d.setCursor(4, 4);
    d.print("BENCH");   // so it is not taken for the press firmware
    d.setTextColor(TFT_WHITE);
    d.setCursor(4, 26);
    d.print("IN ");
    for (int i = 0; i < 8; ++i) d.print(M5StamPLC.readPlcInput(i) ? '1' : '-');
    d.setCursor(4, 48);
    d.print("RL ");
    for (int i = 0; i < 4; ++i) d.print(M5StamPLC.readPlcRelay(i) ? '1' : '-');
    d.setCursor(4, 70);
    d.printf("VIN %.1f V", M5StamPLC.getPowerVoltage());
    d.setCursor(4, 92);
    d.printf("%.1f C", M5StamPLC.getTemp());
    d.setTextSize(1);
    d.setCursor(4, 120);
    d.print("RELAY 1          RELAY 2          RELAY 3");
    Serial.printf("in=");
    for (int i = 0; i < 8; ++i) Serial.print(M5StamPLC.readPlcInput(i) ? '1' : '0');
    Serial.printf(" relay=%d%d%d%d vin=%.2f\n", relays.on[0], relays.on[1], relays.on[2], relays.on[3],
                  M5StamPLC.getPowerVoltage());
}
