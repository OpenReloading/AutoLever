// Native test of the press logic; built and run by tests/test_firmware.py.
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <initializer_list>
#include <string>

#include "../src/logic.h"

using namespace autolever;

#define CHECK(c)                                                         \
    do {                                                                 \
        if (!(c)) {                                                      \
            std::printf("FAIL line %d: %s\n", __LINE__, #c);             \
            std::exit(1);                                                \
        }                                                                \
    } while (0)

// A cylinder that moves 1 mm per 10 ms; home at 0, front at 100.
struct Rig {
    Controller c;
    Inputs in{true, false, true, true, false, false, true};
    Outputs out{};
    uint32_t now = 1000;
    int pos = 0;

    void tick() {
        in.home = pos <= 0;
        in.front = pos >= 100;
        out = c.step(in, now);
        CHECK(!(out.extend && out.retract));
        CHECK(out.enable == (out.extend || out.retract));
        if (out.extend && pos < 100) ++pos;
        if (out.retract && pos > 0) --pos;
        now += 10;
    }
    void run(int n) { while (n--) tick(); }
    // START released for 160 ms, pressed for one step, released again
    void press_start() { in.start = false; run(16); press(); }
    void press() { in.start = true; tick(); in.start = false; tick(); }
    // n failed button reads, carrying the released levels M5Unified reported for a failed read
    void fail(int n) {
        const bool start = in.start, jog = in.jog;
        in.buttons_ok = in.start = in.jog = false;
        run(n);
        in.buttons_ok = true;
        in.start = start;
        in.jog = jog;
    }
    // the rod sticks: the end sensors hold still while the controller runs n steps
    void stick(int n, bool at_home) {
        in.home = at_home;
        in.front = false;
        while (n--) { out = c.step(in, now); now += 10; }
    }
};

// Buttons feeding Controller as loop() does, one loop every 2 ms, on a cylinder that moves 1 mm per loop (home at 0,
// front at 100). A failed read carries 0x00, the all-pressed pattern.
struct Loop {
    Buttons b;
    Controller c;
    uint32_t now = 0;
    int pos = 0;
    bool moved = false;  // an output was on in some loop

    void step(bool read_ok, bool start, bool jog) {
        const uint8_t pressed = (start ? BUTTON_START_BIT : 0) | (jog ? BUTTON_JOG_BIT : 0);
        const Buttons::Levels l = b.step(read_ok, read_ok ? (uint8_t)~pressed : 0x00, now);
        const Outputs out = c.step({pos <= 0, pos >= 100, true, true, l.start, l.jog, l.ok}, now);
        moved = moved || out.enable;
        if (out.extend && pos < 100) ++pos;
        if (out.retract && pos > 0) --pos;
        now += 2;
    }
    void run(int n, bool start, bool jog = false) { while (n--) step(true, start, jog); }
};


// Random operation: whatever the inputs do, the safety rules of the press hold on every step.
static void random_run(uint32_t seed, uint32_t jam_ms) {
    uint32_t rng = seed;
    auto rnd = [&rng](uint32_t n) {   // xorshift32
        rng ^= rng << 13; rng ^= rng >> 17; rng ^= rng << 5;
        return rng % n;
    };
    Controller c;
    c.jam_ms = jam_ms;
    Inputs in{true, false, true, true, false, false, true};
    int pos = 0;
    uint32_t now = 1000, same_since = 0;
    Outputs prev{};
    bool released = false;   // JOG seen released since the press last left Idle
    uint32_t start_up_since = 0, start_up_ms = 0;   // last run of released START reads, as in the controller
    bool prev_start = true;
    State prev_state = State::Idle;
    Fault prev_fault = Fault::None;
    int stuck = 0, failing = 0;
    bool jog = false;
    for (int i = 0; i < 400000; ++i) {
        const bool start = rnd(40) == 0;
        if (rnd(60) == 0) jog = !jog;
        if (failing == 0 && rnd(500) == 0) failing = 1 + (int)rnd(40);   // the button reads fail for a while
        in.buttons_ok = failing == 0;
        if (failing > 0) --failing;
        in.start = in.buttons_ok ? start : rnd(2) == 0;   // a failed read carries any levels
        in.jog = in.buttons_ok ? jog : rnd(2) == 0;
        if (rnd(400) == 0) in.estop_ok = !in.estop_ok;
        if (rnd(700) == 0) in.pressure_ok = !in.pressure_ok;
        if (stuck == 0 && rnd(2000) == 0) stuck = 1 + (int)rnd(3000);   // rod jams for a while
        in.home = pos <= 0;
        in.front = pos >= 100;
        if (rnd(300) == 0) in.home = !in.home;     // sensor glitch
        if (rnd(500) == 0) in.front = !in.front;
        Outputs out = c.step(in, now);
        if (!in.buttons_ok) {
            prev_start = true;
        } else {
            if (!in.start) {
                if (prev_start) start_up_since = now;
                start_up_ms = now - start_up_since;
            }
            prev_start = in.start;
        }

        CHECK(!(out.extend && out.retract));
        CHECK(out.enable == (out.extend || out.retract));   // the feed relay is on only during a stroke
        if (!in.estop_ok || !in.pressure_ok) CHECK(!out.extend && !out.retract && c.state() == State::Fault);
        if (c.state() == State::Idle || c.state() == State::Fault) CHECK(!out.extend && !out.retract);
        if (c.state() == State::Fault) CHECK(c.fault() != Fault::None);
        if (c.state() == State::Jog) CHECK(in.buttons_ok && in.jog);                  // jog moves only while held
        if (prev_state != State::Jog && c.state() == State::Jog) CHECK(released);      // never starts from a held JOG
        if (prev_state != State::Auto && c.state() == State::Auto) {
            CHECK(in.buttons_ok && in.start && start_up_ms >= 150);
        }
        if (prev_state == State::Fault && (prev_fault == Fault::Jam || prev_fault == Fault::Sensor)
            && c.state() != State::Fault) {
            CHECK(in.buttons_ok && in.start);   // only a press acknowledges a jam or a sensor fault
        }
        // one direction never runs longer than the jam timeout, plus the step
        bool on = out.extend || out.retract;
        if (!on || out.extend != prev.extend || out.retract != prev.retract) same_since = now;
        CHECK(!on || now - same_since <= jam_ms);

        if (c.state() != State::Idle || !in.buttons_ok) released = false;
        if (in.buttons_ok && !in.jog) released = true;
        prev_state = c.state();
        prev_fault = c.fault();
        prev = out;
        if (stuck > 0) --stuck;
        else {
            if (out.extend && pos < 100) ++pos;
            if (out.retract && pos > 0) --pos;
        }
        now += 10;
    }
}

int main() {
    {  // auto cycle runs out and back, repeatedly, and counts
        Rig r;
        r.tick();
        CHECK(r.c.state() == State::Idle && !r.out.extend && !r.out.retract);
        r.press_start();
        CHECK(r.c.state() == State::Auto && !r.c.stopping());
        r.run(450);
        CHECK(r.c.cycles() >= 2);
        CHECK(r.c.state() == State::Auto);
    }
    {  // a second press stops after the current stroke, back home
        Rig r;
        r.tick();
        r.press_start();
        r.run(50);
        CHECK(r.pos > 0 && r.pos < 100);
        r.press_start();
        CHECK(r.c.stopping());
        r.run(400);
        CHECK(r.c.state() == State::Idle && r.pos == 0 && r.c.cycles() == 1);
        CHECK(!r.out.extend && !r.out.retract);
    }
    {  // jog moves only while held and cycles
        Rig r;
        r.tick();
        r.in.jog = true;
        r.run(30);
        CHECK(r.c.state() == State::Jog && r.out.extend);
        r.in.jog = false;
        r.tick();
        CHECK(r.c.state() == State::Idle && !r.out.extend && !r.out.retract);
    }
    {  // a jog held at power-up does not start the press
        Rig r;
        r.in.jog = true;
        r.run(10);
        CHECK(r.c.state() == State::Idle && !r.out.extend);
        r.in.jog = false;
        r.tick();
        r.in.jog = true;
        r.tick();
        CHECK(r.c.state() == State::Jog);
    }
    {  // a START held at power-up does not start the press; the next press does
        Rig r;
        r.in.start = true;
        r.run(10);
        CHECK(r.c.state() == State::Idle && !r.out.extend && r.pos == 0);
        r.in.start = false;
        r.tick();
        r.press_start();
        CHECK(r.c.state() == State::Auto && r.out.extend);
    }
    {  // a held START that reads released for less than 150 ms is not a press
        Rig r;
        r.in.start = true;
        r.run(10);
        r.in.start = false;
        r.run(15);  // released reads at 0 to 140 ms
        r.in.start = true;
        r.run(10);
        CHECK(r.c.state() == State::Idle && !r.out.extend && r.pos == 0);
        r.in.start = false;
        r.run(16);  // 0 to 150 ms
        r.in.start = true;
        r.tick();
        CHECK(r.c.state() == State::Auto && r.out.extend);
    }
    {  // START held through 150 ms or more of failed button reads (only the button expander fails) is not a press
        Rig r;
        r.in.start = true;
        r.run(10);
        r.fail(20);  // failed reads at 0 to 190 ms
        r.run(10);
        CHECK(r.c.state() == State::Idle && !r.out.extend && r.pos == 0);
        r.press_start();  // good reads after the failures: as before
        CHECK(r.c.state() == State::Auto && r.out.extend);
    }
    {  // a 0.3 s bus stall that spans two failed button reads with START held is not a press
        Rig r;
        r.in.start = true;
        r.run(10);
        r.fail(1);
        r.now += 300;  // the loop stalls on the bus
        r.fail(1);
        r.run(10);
        CHECK(r.c.state() == State::Idle && !r.out.extend && r.pos == 0);
        r.press_start();
        CHECK(r.c.state() == State::Auto && r.out.extend);
    }
    {  // a failed read between a release and a press ends the release: START needs 150 ms of good reads again
        Rig r;
        r.tick();
        r.in.start = false;
        r.run(16);  // released 0 to 150 ms
        r.fail(1);
        r.in.start = true;
        r.tick();
        CHECK(r.c.state() == State::Idle && !r.out.extend && r.pos == 0);
        r.press_start();
        CHECK(r.c.state() == State::Auto && r.out.extend);
    }
    {  // JOG held through failed reads is not armed by them; released and pressed on good reads, it jogs as before
        Rig r;
        r.in.jog = true;
        r.run(5);  // held at power-up: not armed
        r.fail(3);
        r.run(5);
        CHECK(r.c.state() == State::Idle && !r.out.extend && r.pos == 0);
        r.in.jog = false;
        r.tick();
        r.in.jog = true;
        r.tick();
        CHECK(r.c.state() == State::Jog && r.out.extend);
    }
    {  // a failed read between a JOG release and a press disarms it
        Rig r;
        r.tick();  // JOG released: armed
        r.fail(1);
        r.in.jog = true;
        r.run(5);
        CHECK(r.c.state() == State::Idle && !r.out.extend && r.pos == 0);
        r.in.jog = false;
        r.tick();
        r.in.jog = true;
        r.tick();
        CHECK(r.c.state() == State::Jog && r.out.extend);
    }
    {  // a failed read stops a JOG whatever levels it carries; the JOG needs a release and a press after it
        Rig r;
        r.tick();
        r.in.jog = true;
        r.run(10);
        CHECK(r.c.state() == State::Jog && r.out.extend);
        r.in.buttons_ok = false;  // still carries JOG held
        r.tick();
        CHECK(r.c.state() == State::Idle && !r.out.extend && !r.out.retract);
        r.in.buttons_ok = true;
        r.run(5);
        CHECK(r.c.state() == State::Idle && !r.out.extend && !r.out.retract);
        r.in.jog = false;
        r.tick();
        r.in.jog = true;
        r.tick();
        CHECK(r.c.state() == State::Jog);
    }
    {  // failed reads with START held do not acknowledge a sensor fault; a press on good reads does
        Rig r;
        r.in.start = true;
        r.in.home = r.in.front = true;
        r.out = r.c.step(r.in, r.now);
        CHECK(r.c.fault() == Fault::Sensor);
        r.run(3);  // sensors sane again, START still held
        r.fail(3);
        r.run(3);
        CHECK(r.c.state() == State::Fault && r.c.fault() == Fault::Sensor && !r.out.extend && !r.out.retract);
        r.press_start();
        CHECK(r.c.state() == State::Idle && r.c.fault() == Fault::None);
    }
    {  // in AUTO a failed read requests the stop; START still held on the good reads after it does not restart
        Rig r;
        r.tick();
        r.press_start();
        r.run(20);
        CHECK(r.c.state() == State::Auto && !r.c.stopping());
        r.in.start = true;
        r.fail(1);
        CHECK(r.c.state() == State::Auto && r.c.stopping());
        r.run(300);  // START held on good reads for 3 s
        CHECK(r.c.state() == State::Idle && r.pos == 0 && !r.out.enable && r.c.cycles() == 1);
    }
    {  // reads failing for good in AUTO: the press finishes the cycle, returns home and stays in IDLE
        Rig r;
        r.tick();
        r.press_start();
        r.run(20);
        r.fail(1000);  // 10 s
        CHECK(r.c.state() == State::Idle && r.pos == 0 && !r.out.enable && r.c.cycles() == 1);
    }
    {  // a 10 ms release still stops AUTO after the stroke
        Rig r;
        r.tick();
        r.press_start();  // ends with one released step
        r.press();
        CHECK(r.c.stopping());
    }
    {  // E-STOP: valves off, idle after the reset until button A
        Rig r;
        r.tick();
        r.press_start();
        r.run(50);
        r.in.estop_ok = false;
        r.tick();
        CHECK(r.c.state() == State::Fault && r.c.fault() == Fault::EStop && !r.out.extend && !r.out.retract);
        r.in.estop_ok = true;
        r.run(5);
        CHECK(r.c.state() == State::Idle && !r.out.extend && !r.out.retract);
    }
    {  // pressure trip is its own fault
        Rig r;
        r.in.pressure_ok = false;
        r.tick();
        CHECK(r.c.fault() == Fault::Pressure);
    }
    {  // jam: one stroke longer than the timeout stops everything until acknowledged
        Rig r;
        r.c.jam_ms = 500;
        r.tick();
        r.press_start();
        r.run(20);
        r.pos = 40;  // the rod sticks
        r.stick(100, false);
        CHECK(r.c.state() == State::Fault && r.c.fault() == Fault::Jam && !r.out.extend && !r.out.retract);
        r.run(5);
        CHECK(r.c.state() == State::Fault);
        r.press_start();  // acknowledge, stays idle
        CHECK(r.c.state() == State::Idle);
        r.press_start();
        CHECK(r.c.state() == State::Auto);
    }
    {  // a stall at home is a jam too
        Rig r;
        r.c.jam_ms = 500;
        r.tick();
        r.press_start();
        r.stick(100, true);  // valve on, rod does not leave home
        CHECK(r.c.fault() == Fault::Jam);
    }
    {  // the jam timer holds across the 32-bit millis wrap
        Rig r;
        r.c.jam_ms = 500;
        r.now = UINT32_MAX - 470;
        r.run(17);
        const uint32_t start = r.now;
        r.press();  // the stroke starts at `start`
        while (r.now - start <= r.c.jam_ms) {  // the rod sticks
            r.out = r.c.step(r.in, r.now);
            CHECK(r.c.state() == State::Auto && r.out.extend);
            r.now += 10;
        }
        CHECK(r.now < start);  // the counter wrapped before the timeout
        r.out = r.c.step(r.in, r.now);
        CHECK(r.c.fault() == Fault::Jam && !r.out.extend && !r.out.retract);
    }
    {  // both end sensors on is a sensor fault; clears on button A once they are sane
        Rig r;
        r.in.home = r.in.front = true;
        r.out = r.c.step(r.in, r.now);
        CHECK(r.c.fault() == Fault::Sensor && !r.out.extend && !r.out.retract);
        r.in.front = false;
        r.in.start = true;
        r.out = r.c.step(r.in, r.now + 10);
        CHECK(r.c.state() == State::Idle);
    }
    {  // a jam stays latched under an E-STOP and still needs button A after the release
        Rig r;
        r.c.jam_ms = 500;
        r.tick();
        r.press_start();
        r.stick(100, true);  // valve on, rod does not leave home
        CHECK(r.c.fault() == Fault::Jam);
        r.in.estop_ok = false;
        r.run(5);
        CHECK(r.c.state() == State::Fault && r.c.fault() == Fault::EStop);
        r.in.estop_ok = true;
        r.run(5);
        CHECK(r.c.state() == State::Fault && r.c.fault() == Fault::Jam && !r.out.extend && !r.out.retract);
        r.press_start();  // acknowledge, stays idle
        CHECK(r.c.state() == State::Idle && r.c.fault() == Fault::None);
        r.press_start();
        CHECK(r.c.state() == State::Auto);
    }
    {  // a sensor fault stays latched under a pressure loss and still needs button A after recovery
        Rig r;
        r.in.home = r.in.front = true;
        r.out = r.c.step(r.in, r.now);
        CHECK(r.c.fault() == Fault::Sensor);
        r.in.front = false;
        r.in.pressure_ok = false;
        r.run(5);
        CHECK(r.c.state() == State::Fault && r.c.fault() == Fault::Pressure);
        r.in.pressure_ok = true;
        r.run(5);
        CHECK(r.c.state() == State::Fault && r.c.fault() == Fault::Sensor && !r.out.extend && !r.out.retract);
        r.press_start();
        CHECK(r.c.state() == State::Idle && r.c.fault() == Fault::None);
    }
    {  // A during a supply fault does not acknowledge a latched jam; it survives E-STOP and pressure loss stacked
        Rig r;
        r.c.jam_ms = 500;
        r.tick();
        r.press_start();
        r.stick(100, false);  // valve on, the rod stops just off home
        CHECK(r.c.fault() == Fault::Jam);
        r.in.estop_ok = false;
        r.tick();
        r.press_start();
        r.in.pressure_ok = false;
        r.run(5);
        r.in.estop_ok = true;
        r.run(5);
        CHECK(r.c.fault() == Fault::Pressure);
        r.in.pressure_ok = true;
        r.run(5);
        CHECK(r.c.state() == State::Fault && r.c.fault() == Fault::Jam && !r.out.extend && !r.out.retract);
        r.press_start();
        CHECK(r.c.state() == State::Idle);
    }
    {  // JOG held through an E-STOP does not move the press after the release
        Rig r;
        r.tick();
        r.in.jog = true;
        r.run(30);
        CHECK(r.c.state() == State::Jog);
        r.in.estop_ok = false;
        r.tick();
        r.in.estop_ok = true;
        r.run(20);
        CHECK(r.c.state() == State::Idle && !r.out.extend && !r.out.retract);
        r.in.jog = false;
        r.tick();
        r.in.jog = true;
        r.tick();
        CHECK(r.c.state() == State::Jog && r.out.retract);   // mid-stroke: back home first
    }
    {  // the feed relay: off at idle, on through the strokes, off at a jam, an E-STOP and a stop at home
        Rig r;
        r.c.jam_ms = 1500;   // one stroke takes 1000 ms
        r.tick();
        CHECK(!r.out.enable);
        r.press_start();
        CHECK(r.out.enable && r.out.extend);
        r.run(150);   // out to the front and on the way back
        CHECK(r.out.enable && r.out.retract);
        r.stick(200, false);
        CHECK(r.c.fault() == Fault::Jam && !r.out.enable);
        r.press_start();
        r.press_start();
        CHECK(r.c.state() == State::Auto && r.out.enable);
        r.in.estop_ok = false;
        r.tick();
        CHECK(r.c.fault() == Fault::EStop && !r.out.enable);
        r.in.estop_ok = true;
        r.tick();
        r.press_start();
        r.run(20);
        r.press_start();   // stop request
        r.run(400);
        CHECK(r.c.state() == State::Idle && !r.out.enable);
    }
    {  // starting mid-stroke retracts first
        Rig r;
        r.pos = 50;
        r.tick();
        r.press_start();
        CHECK(r.out.retract && !r.out.extend);
    }
    {  // settings posts: only from the page's own host, or without Origin and Referer
        CHECK(same_origin("", "192.168.4.1"));
        CHECK(same_origin("http://192.168.4.1", "192.168.4.1"));
        CHECK(same_origin("http://AutoLever.local/", "autolever.local"));
        CHECK(same_origin("http://192.168.1.20:80/settings", "192.168.1.20:80"));
        CHECK(!same_origin("https://evil.example", "192.168.4.1"));
        CHECK(!same_origin("http://192.168.4.10", "192.168.4.1"));
        CHECK(!same_origin("http://192.168.4.1", "192.168.4.10"));
        CHECK(!same_origin("null", "192.168.4.1"));
        CHECK(!same_origin("http://autolever.local", ""));
        CHECK(same_origin(nullptr, "192.168.4.1") && same_origin(nullptr, nullptr));
        CHECK(!same_origin("http://autolever.local", nullptr));
    }
    for (uint32_t seed : {1u, 2u, 3u, 12345u}) random_run(seed, 800);
    {  // names on the display and the status page
        CHECK(!std::strcmp(state_name(State::Idle), "IDLE") && !std::strcmp(state_name(State::Auto), "AUTO"));
        CHECK(!std::strcmp(state_name(State::Jog), "JOG") && !std::strcmp(state_name(State::Fault), "FAULT"));
        CHECK(!std::strcmp(fault_name(Fault::None), "") && !std::strcmp(fault_name(Fault::EStop), "E-STOP"));
        CHECK(!std::strcmp(fault_name(Fault::Pressure), "PRESSURE") && !std::strcmp(fault_name(Fault::Sensor), "SENSOR"));
        CHECK(!std::strcmp(fault_name(Fault::Jam), "JAM"));
    }
    CHECK(jam_ms_from_seconds(0) == 2000 && jam_ms_from_seconds(-5) == 2000);
    CHECK(jam_ms_from_seconds(15) == 15000 && jam_ms_from_seconds(500) == 120000);
    CHECK(jam_ms_from_seconds(UINT32_MAX / 1000) == 120000);   // a corrupt stored value at boot
    {  // settings form field: empty or non-numeric leaves the value unchanged
        uint32_t ms = 7000;
        CHECK(!jam_ms_from_text("", ms) && !jam_ms_from_text("abc", ms) && !jam_ms_from_text("15s", ms));
        CHECK(!jam_ms_from_text("1.5", ms) && !jam_ms_from_text(nullptr, ms) && ms == 7000);
        CHECK(jam_ms_from_text("15", ms) && ms == 15000);
        CHECK(jam_ms_from_text("0", ms) && ms == 2000 && jam_ms_from_text("500", ms) && ms == 120000);
    }
    {  // Wi-Fi form password: empty keeps the stored one, else a WPA2 passphrase length
        CHECK(wifi_pass_ok(nullptr) && wifi_pass_ok("") && wifi_pass_ok("12345678") && wifi_pass_ok(std::string(63, 'a').c_str()));
        CHECK(!wifi_pass_ok("1") && !wifi_pass_ok("1234567") && !wifi_pass_ok(std::string(64, 'a').c_str()));
    }
    {  // button register: a pressed button reads 0, START on bit 2, JOG on bit 1; a new level counts after 10 ms
        Buttons b;
        Buttons::Levels l = b.step(true, 0xFF, 0);
        CHECK(!l.ok);  // one read settles nothing
        l = b.step(true, 0xFF, 10);
        CHECK(l.ok && !l.start && !l.jog);
        l = b.step(true, 0xFB, 20);
        CHECK(l.ok && !l.start && !l.jog);  // START down for 0 ms: still released
        l = b.step(true, 0xFB, 29);
        CHECK(l.ok && !l.start);
        l = b.step(true, 0xFB, 30);
        CHECK(l.ok && l.start && !l.jog);
        l = b.step(true, 0xF9, 40);
        l = b.step(true, 0xF9, 50);
        CHECK(l.ok && l.start && l.jog);
        l = b.step(true, 0xFD, 60);
        l = b.step(true, 0xFD, 70);
        CHECK(l.ok && !l.start && l.jog);
        l = b.step(true, 0xFE, 80);   // button C only
        l = b.step(true, 0xFE, 90);
        CHECK(l.ok && !l.start && !l.jog);
    }
    {  // a bounce shorter than 10 ms does not change the level
        Buttons b;
        b.step(true, 0xFF, 0);
        b.step(true, 0xFF, 10);
        b.step(true, 0xFB, 20);
        b.step(true, 0xFF, 25);
        b.step(true, 0xFB, 28);
        Buttons::Levels l = b.step(true, 0xFB, 35);
        CHECK(l.ok && !l.start);  // down again since 28 ms
        l = b.step(true, 0xFB, 38);
        CHECK(l.ok && l.start);
    }
    {  // a failed read makes both levels unknown at once, until good reads have shown a level for 10 ms
        Buttons b;
        b.step(true, 0xFB, 0);
        CHECK(b.step(true, 0xFB, 10).start);
        Buttons::Levels l = b.step(false, 0x00, 20);
        CHECK(!l.ok && !l.start && !l.jog);
        l = b.step(true, 0xFB, 30);
        CHECK(!l.ok);
        l = b.step(true, 0xFB, 40);
        CHECK(l.ok && l.start && !l.jog);
    }
    {  // START or JOG held from power-up, through any pattern of failed reads or none, moves nothing
        for (int button = 0; button < 2; ++button)
            for (int burst : {0, 1, 2, 5, 10, 75, 100})      // failed reads in a row
                for (int gap : {1, 2, 5, 6, 10, 75, 200}) {  // good reads between
                    Loop p;
                    for (int i = 0; i < 2500; ++i) p.step(i % (burst + gap) >= burst, button == 0, button == 1);
                    CHECK(!p.moved && p.c.state() == State::Idle);
                }
    }
    {  // AUTO with one failed read every 8 to 24 ms and a 300 ms START press at any phase of it: IDLE at home
        for (int period = 4; period <= 12; ++period)  // loops
            for (int phase = 0; phase < period; ++phase) {
                Loop p;
                p.run(100, false);
                p.run(10, true);
                p.run(100, false);
                CHECK(p.c.state() == State::Auto);
                for (int i = 0; i < 1000; ++i) p.step(i % period != 0, i >= 50 + phase && i < 200 + phase, false);
                CHECK(p.c.state() == State::Idle && p.pos == 0);
            }
    }
    {  // across the millis() wrap: START settles after 10 ms of good reads, and AUTO needs 150 ms released before it
        struct Case { uint32_t now; int released, held; State state; };
        const Case cases[] = {
            {UINT32_MAX - 199, 95, 5, State::Idle},  // pressed from 9 ms before the wrap, 5 reads (8 ms)
            {UINT32_MAX - 199, 95, 6, State::Auto},  // 6 reads (10 ms)
            {UINT32_MAX - 79, 70, 6, State::Idle},   // released 138 ms across the wrap
            {UINT32_MAX - 79, 80, 6, State::Auto},   // released 158 ms across the wrap
        };
        for (const Case& k : cases) {
            Loop p;
            p.now = k.now;
            p.run(k.released, false);
            p.run(k.held, true);
            CHECK(p.c.state() == k.state);
        }
    }
    {  // relay readback: a relay commanded off that reads on restarts after more than 100 ms in a row
        RelayCheck k;
        CHECK(!k.stuck(true, 0x1, 0x1, 0));     // extend on, reads on
        CHECK(!k.stuck(true, 0x0, 0x1, 10));    // commanded on, reads off: the jam timer covers it
        CHECK(!k.stuck(true, 0x1, 0x0, 20));
        CHECK(!k.stuck(true, 0x1, 0x0, 120));
        CHECK(k.stuck(true, 0x1, 0x0, 121));
    }
    {  // a clean read in between starts the count again
        RelayCheck k;
        CHECK(!k.stuck(true, 0x2, 0x0, 0));
        CHECK(!k.stuck(true, 0x0, 0x0, 90));
        CHECK(!k.stuck(true, 0x2, 0x0, 150));
        CHECK(!k.stuck(true, 0x2, 0x0, 250));
        CHECK(k.stuck(true, 0x2, 0x0, 251));
    }
    {  // a failed expander read counts as stuck: it reads as all off
        RelayCheck k;
        CHECK(!k.stuck(false, 0x0, 0x0, 0));
        CHECK(k.stuck(false, 0x0, 0x0, 101));
    }
    {  // relay write order (relay number, minus for off): relay 3 opens first and closes last, also for the all-off
       // write before a restart on a stuck readback
        struct Case { Outputs out; int order[3]; };
        const Case cases[] = {
            {{false, false, false}, {-3, -1, -2}},
            {{true, false, true}, {-2, 1, 3}},
            {{false, true, true}, {-1, 2, 3}},
        };
        for (const Case& c : cases) {
            int order[3] = {}, n = 0;
            write_relays(c.out, [&](uint8_t relay, bool on) {
                CHECK(n < 3);
                order[n++] = on ? relay + 1 : -(relay + 1);
            });
            CHECK(n == 3 && std::memcmp(order, c.order, sizeof order) == 0);
        }
    }
    {  // updates: closed until button C is held, then open for 10 minutes
        UpdateWindow w;
        CHECK(!w.is_open(0) && !w.is_open(5000));
        w.open(4294700000u);   // 267296 ms before the millis() wrap
        CHECK(w.is_open(4294700000u) && w.is_open(4294967295u) && w.is_open(332703u));
        CHECK(!w.is_open(332704u));   // 600000 ms after open()
        CHECK(!w.is_open(4294700000u) && !w.is_open(4294700001u));   // one wrap later, still closed
        w.open(100);   // held again
        CHECK(w.is_open(100) && w.is_open(600099) && !w.is_open(600100));
    }
    std::puts("ok");
    return 0;
}
