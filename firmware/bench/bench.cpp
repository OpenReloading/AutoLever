// Bench image: shows the 8 inputs live and switches the relays, to check the wiring before the press firmware runs.
//   A, B, C toggle relays 1, 2, 3. Hold A and C together to switch all relays off. Build and flash: pio run -e bench -t upload
#include <M5StamPLC.h>

static bool relay[4];

void setup() {
    M5StamPLC.begin();
    Serial.begin(115200);
    M5StamPLC.writePlcAllRelay(0);
}

void loop() {
    M5StamPLC.update();
    bool changed = false;
    for (int i = 0; i < 3; ++i) {
        auto& b = i == 0 ? M5StamPLC.BtnA() : i == 1 ? M5StamPLC.BtnB() : M5StamPLC.BtnC();
        if (b.wasPressed()) {
            relay[i] = !relay[i];
            changed = true;
        }
    }
    if (M5StamPLC.BtnA().isPressed() && M5StamPLC.BtnC().isPressed()) {
        for (bool& r : relay) r = false;
        changed = true;
    }
    if (changed) for (int i = 0; i < 4; ++i) M5StamPLC.writePlcRelay(i, relay[i]);

    static uint32_t last = 0;
    if (millis() - last < 200) return;
    last = millis();
    auto& d = M5StamPLC.Display();
    d.fillScreen(TFT_BLACK);
    d.setTextColor(TFT_WHITE);
    d.setTextSize(2);
    d.setCursor(4, 4);
    d.print("IN ");
    for (int i = 0; i < 8; ++i) d.print(M5StamPLC.readPlcInput(i) ? '1' : '-');
    d.setCursor(4, 30);
    d.print("RL ");
    for (int i = 0; i < 4; ++i) d.print(M5StamPLC.readPlcRelay(i) ? '1' : '-');
    d.setCursor(4, 56);
    d.printf("VIN %.1f V", M5StamPLC.getPowerVoltage());
    d.setCursor(4, 82);
    d.printf("%.1f C", M5StamPLC.getTemp());
    d.setTextSize(1);
    d.setCursor(4, 120);
    d.print("RELAY 1          RELAY 2          RELAY 3");
    Serial.printf("in=");
    for (int i = 0; i < 8; ++i) Serial.print(M5StamPLC.readPlcInput(i) ? '1' : '0');
    Serial.printf(" relay=%d%d%d%d vin=%.2f\n", relay[0], relay[1], relay[2], relay[3], M5StamPLC.getPowerVoltage());
}
