#include <M5StamPLC.h>
#include <Preferences.h>

#include "logic.h"

using namespace autolever;

// Input channels (0 to 7) and relays (0 to 3) as wired in the control box.
constexpr uint8_t IN_HOME = 0, IN_FRONT = 1, IN_ESTOP_OK = 2, IN_PRESSURE_OK = 3;
constexpr uint8_t RELAY_EXTEND = 0, RELAY_RETRACT = 1;

static Controller press;
static Preferences prefs;
static State shown_state = State::Fault;
static Fault shown_fault = Fault::None;
static uint32_t shown_cycles = UINT32_MAX;
static bool info_screen = false;
static bool redraw = true;

static const char* state_name(State s) {
    switch (s) {
        case State::Idle: return "IDLE";
        case State::Auto: return "AUTO";
        case State::Jog: return "JOG";
        default: return "FAULT";
    }
}

static const char* fault_name(Fault f) {
    switch (f) {
        case Fault::EStop: return "E-STOP";
        case Fault::Pressure: return "PRESSURE";
        case Fault::Sensor: return "SENSOR";
        case Fault::Jam: return "JAM";
        default: return "";
    }
}

static void draw() {
    auto& d = M5StamPLC.Display();
    d.fillScreen(TFT_BLACK);
    d.setTextColor(TFT_WHITE);
    d.setTextSize(2);
    d.setCursor(4, 4);
    d.printf("%s", info_screen ? "INFO" : state_name(press.state()));
    d.setCursor(4, 30);
    if (info_screen) d.printf("Cycles %lu\nJam %lu s", (unsigned long)press.cycles(), (unsigned long)(press.jam_ms / 1000));
    else d.printf("%s%s", fault_name(press.fault()), press.stopping() ? "STOPPING" : "");
    if (!info_screen) {
        d.setCursor(4, 56);
        d.printf("Cycles %lu", (unsigned long)press.cycles());
    }
    d.setTextSize(1);
    d.setCursor(4, 120);
    d.print("START/STOP   JOG    INFO");
}

void setup() {
    M5StamPLC.begin();
    M5StamPLC.writePlcAllRelay(0);
    prefs.begin("autolever");
    press.set_cycles(prefs.getUInt("cycles", 0));
    press.jam_ms = prefs.getUInt("jam_ms", press.jam_ms);
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
    Outputs out = press.step(in, millis());
    if (M5StamPLC.readPlcRelay(RELAY_EXTEND) != out.extend) M5StamPLC.writePlcRelay(RELAY_EXTEND, out.extend);
    if (M5StamPLC.readPlcRelay(RELAY_RETRACT) != out.retract) M5StamPLC.writePlcRelay(RELAY_RETRACT, out.retract);

    if (press.cycles() != shown_cycles) {
        if (shown_cycles != UINT32_MAX) prefs.putUInt("cycles", press.cycles());
        shown_cycles = press.cycles();
        redraw = true;
    }
    if (press.state() != shown_state || press.fault() != shown_fault) {
        if (press.state() == State::Fault) M5StamPLC.tone(2000, 200);
        shown_state = press.state();
        shown_fault = press.fault();
        redraw = true;
    }
    if (redraw) {
        draw();
        redraw = false;
    }
}
