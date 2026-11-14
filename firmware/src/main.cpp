#include <M5StamPLC.h>
#include <Preferences.h>

#include <mutex>

#include "logic.h"
#include "web.h"

using namespace autolever;

// Input channels (0 to 7) as wired in the control box; the relays are in logic.h.
// The inputs are opto-isolated with anti-parallel LEDs (EL3H4), so either polarity works, and the expander reads
// true while an input is driven. All eight share COM (terminal C): connect it to 0 V for PNP sensors.
constexpr uint8_t IN_HOME = 0, IN_FRONT = 1, IN_ESTOP_OK = 2, IN_PRESSURE_OK = 3;

static Controller press;
static RelayCheck relay_check;
static UpdateWindow update_window;
static Preferences prefs;
static std::mutex press_lock;   // press, shared with the web task
static State shown_state = State::Fault;
static Fault shown_fault = Fault::None;
static bool shown_stopping = false;
static uint32_t shown_cycles = UINT32_MAX;
static bool info_screen = false;
static bool redraw = true;

// The loop watchdog restarts the unit only with these two values of the prebuilt core config.
#ifndef CONFIG_ESP_TASK_WDT_PANIC
#error "the loop watchdog needs CONFIG_ESP_TASK_WDT_PANIC"
#endif
static_assert(CONFIG_ESP_TASK_WDT_TIMEOUT_S == 5, "loop watchdog timeout");

// Why the unit last started: after a watchdog or readback restart it comes back in IDLE as after power-up.
static const char* reset_name(esp_reset_reason_t r) {
    static const struct { esp_reset_reason_t reason; const char* name; } names[] = {
        {ESP_RST_POWERON, "power-on"},
        {ESP_RST_SW, "restart"},   // ESP.restart(): relay readback, or after an update
        {ESP_RST_PANIC, "panic"},
        {ESP_RST_TASK_WDT, "watchdog"},
        {ESP_RST_INT_WDT, "int watchdog"},
        {ESP_RST_BROWNOUT, "brownout"},
    };
    for (const auto& n : names) {
        if (n.reason == r) return n.name;
    }
    return nullptr;
}

static void draw() {
    std::lock_guard<std::mutex> hold(press_lock);
    auto& d = M5StamPLC.Display();
    d.fillScreen(TFT_BLACK);
    d.setTextColor(TFT_WHITE);
    d.setTextSize(info_screen ? 1 : 2);
    d.setCursor(4, 4);
    if (info_screen) {
        d.printf("INFO\nWi-Fi  %s\nPass   %s\nPhone  192.168.4.1\nHome   %s\nName   autolever.local\n"
                 "Cycles %lu   Jam %lu s\nUpdate %s\nReset  ",
                 web_ap_ssid().c_str(), web_ap_password().c_str(), web_ip().c_str(),
                 (unsigned long)press.cycles(), (unsigned long)(press.jam_ms / 1000),
                 update_window.is_open(millis()) ? "open" : "closed, hold C");
        const esp_reset_reason_t reason = esp_reset_reason();   // fixed for the whole boot
        if (const char* name = reset_name(reason)) d.print(name);
        else d.printf("code %d", (int)reason);
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
    M5StamPLC.BtnC().setHoldThresh(2000);
    prefs.begin("autolever");
    press.set_cycles(prefs.getUInt("cycles", 0));
    press.jam_ms = jam_ms_from_seconds(prefs.getUInt("jam_ms", press.jam_ms) / 1000);
    web_begin(press, prefs, press_lock);
    // A loop() stalled for 5 s panics and restarts the unit (CONFIG_ESP_TASK_WDT_PANIC); begin() sets every relay off.
    enableLoopWDT();
}

void loop() {
    M5StamPLC.update();
    if (M5StamPLC.BtnC().wasClicked()) {   // on release, so a hold does not also toggle the screen
        info_screen = !info_screen;
        redraw = true;
    }
    if (M5StamPLC.BtnC().wasHold()) {
        update_window.open(millis());
        M5StamPLC.tone(4000, 100);
        info_screen = true;
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
    write_relays(out, set_relay);
    // Relays 0 to 3 are pins 0 to 3 of the expander's input port 0 (register 0x00).
    uint8_t read = 0;
    bool read_ok = M5StamPLC.getIOExpanderB().readRegister(0x00, &read, 1);
    uint8_t commanded = out.extend << RELAY_EXTEND | out.retract << RELAY_RETRACT | out.enable << RELAY_ENABLE;
    if (relay_check.stuck(read_ok, read & 0x0F, commanded, millis())) {
        // The restart does not reset the expander and begin() only clears it after boot, so relay 3 opens first.
        // Written without set_relay's read, which reads off when the expander read fails.
        write_relays(Outputs{}, [](uint8_t relay, bool on) { M5StamPLC.writePlcRelay(relay, on); });
        ESP.restart();
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
#ifdef AUTOLEVER_HANG_TEST
    if (shown_state == State::Auto) for (;;) delay(10);   // bench check: hangs with the extend valve on
#endif
    // after the relays: an OTA upload holds the loop; the window is evaluated every loop so its latch expires
    web_loop(update_window.is_open(millis()) && shown_state == State::Idle, read_ok && !(read & 0x0F));

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
