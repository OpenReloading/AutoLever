#include <M5StamPLC.h>
#include <Preferences.h>

#include <mutex>

#include "logic.h"
#include "web.h"

using namespace autolever;

// Input channels (0 to 7) and relays (0 to 3) as wired in the control box.
// The inputs are opto-isolated with anti-parallel LEDs (EL3H4), so either polarity works, and the expander reads
// true while an input is driven. All eight share COM (terminal C): connect it to 0 V for PNP sensors.
constexpr uint8_t IN_HOME = 0, IN_FRONT = 1, IN_ESTOP_OK = 2, IN_PRESSURE_OK = 3;
constexpr uint8_t RELAY_EXTEND = 0, RELAY_RETRACT = 1;

static Controller press;
static Preferences prefs;
static std::mutex press_lock;   // press and prefs, shared with the web task
static State shown_state = State::Fault;
static Fault shown_fault = Fault::None;
static bool shown_stopping = false;
static uint32_t shown_cycles = UINT32_MAX;
static bool info_screen = false;
static bool redraw = true;

static void draw() {
    std::lock_guard<std::mutex> hold(press_lock);
    auto& d = M5StamPLC.Display();
    d.fillScreen(TFT_BLACK);
    d.setTextColor(TFT_WHITE);
    d.setTextSize(info_screen ? 1 : 2);
    d.setCursor(4, 4);
    if (info_screen) {
        d.printf("INFO\nWi-Fi  %s\nPass   %s\nPhone  192.168.4.1\nHome   %s\nName   autolever.local\n"
                 "Cycles %lu   Jam %lu s",
                 web_ap_ssid().c_str(), web_ap_password().c_str(), web_ip().c_str(),
                 (unsigned long)press.cycles(), (unsigned long)(press.jam_ms / 1000));
    } else {
        d.printf("%s\n%s%s\nCycles %lu", state_name(press.state()), fault_name(press.fault()),
                 press.stopping() ? "STOPPING" : "", (unsigned long)press.cycles());
    }
    d.setTextSize(1);
    d.setCursor(4, 120);
    d.print("START/STOP   JOG    INFO");
}

static void set_relay(uint8_t relay, bool on) {
    if (M5StamPLC.readPlcRelay(relay) != on) M5StamPLC.writePlcRelay(relay, on);
}

void setup() {
    M5StamPLC.begin();
    M5StamPLC.writePlcAllRelay(0);
    prefs.begin("autolever");
    press.set_cycles(prefs.getUInt("cycles", 0));
    press.jam_ms = jam_ms_from_seconds(prefs.getUInt("jam_ms", press.jam_ms) / 1000);
    web_begin(press, prefs, press_lock);
}

void loop() {
    M5StamPLC.update();
    if (M5StamPLC.BtnC().wasPressed()) {
        info_screen = !info_screen;
        redraw = true;
    }

    Inputs in{
        M5StamPLC.readPlcInput(IN_HOME),
        M5StamPLC.readPlcInput(IN_FRONT),
        M5StamPLC.readPlcInput(IN_ESTOP_OK),
        M5StamPLC.readPlcInput(IN_PRESSURE_OK),
        M5StamPLC.BtnA().isPressed(),
        M5StamPLC.BtnB().isPressed(),
    };
    std::unique_lock<std::mutex> hold(press_lock);
    Outputs out = press.step(in, millis());
    hold.unlock();
    // The relay that turns off is written first, so extend and retract are never on together.
    if (out.extend) {
        set_relay(RELAY_RETRACT, out.retract);
        set_relay(RELAY_EXTEND, true);
    } else {
        set_relay(RELAY_EXTEND, false);
        set_relay(RELAY_RETRACT, out.retract);
    }

    hold.lock();
    if (press.cycles() != shown_cycles) {
        if (shown_cycles != UINT32_MAX) prefs.putUInt("cycles", press.cycles());   // also after a reset from the page
        shown_cycles = press.cycles();
        redraw = true;
    }
    if (press.state() != shown_state || press.fault() != shown_fault || press.stopping() != shown_stopping) {
        if (press.state() == State::Fault) M5StamPLC.tone(2000, 200);
        shown_state = press.state();
        shown_fault = press.fault();
        shown_stopping = press.stopping();
        redraw = true;
    }
    hold.unlock();
    web_loop(shown_state == State::Idle);   // after the relays: an OTA upload holds the loop

    static uint32_t last_info = 0;   // the home address arrives some seconds after power-up
    if (info_screen && millis() - last_info > 2000) {
        last_info = millis();
        redraw = true;
    }
    if (redraw) {
        draw();
        redraw = false;
    }
}
