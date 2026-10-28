// Native test of the press logic; built and run by tests/test_firmware.py.
#include <cstdio>
#include <cstdlib>
#include <initializer_list>

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
    Inputs in{true, false, true, true, false, false};
    Outputs out{};
    uint32_t now = 1000;
    int pos = 0;

    void tick() {
        in.home = pos <= 0;
        in.front = pos >= 100;
        out = c.step(in, now);
        CHECK(!(out.extend && out.retract));
        if (out.extend && pos < 100) ++pos;
        if (out.retract && pos > 0) --pos;
        now += 10;
    }
    void run(int n) { while (n--) tick(); }
    void press_start() { in.start = true; tick(); in.start = false; tick(); }
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
    Inputs in{true, false, true, true, false, false};
    int pos = 0;
    uint32_t now = 1000, same_since = 0;
    Outputs prev{};
    bool released = false;   // JOG seen released since the press last left Idle
    State prev_state = State::Idle;
    int stuck = 0;
    for (int i = 0; i < 400000; ++i) {
        in.start = rnd(40) == 0;
        if (rnd(60) == 0) in.jog = !in.jog;
        if (rnd(400) == 0) in.estop_ok = !in.estop_ok;
        if (rnd(700) == 0) in.pressure_ok = !in.pressure_ok;
        if (stuck == 0 && rnd(2000) == 0) stuck = 1 + (int)rnd(3000);   // rod jams for a while
        in.home = pos <= 0;
        in.front = pos >= 100;
        if (rnd(300) == 0) in.home = !in.home;     // sensor glitch
        if (rnd(500) == 0) in.front = !in.front;
        Outputs out = c.step(in, now);

        CHECK(!(out.extend && out.retract));
        if (!in.estop_ok || !in.pressure_ok) CHECK(!out.extend && !out.retract && c.state() == State::Fault);
        if (c.state() == State::Idle || c.state() == State::Fault) CHECK(!out.extend && !out.retract);
        if (c.state() == State::Fault) CHECK(c.fault() != Fault::None);
        if (c.state() == State::Jog) CHECK(in.jog);                                   // jog moves only while held
        if (prev_state != State::Jog && c.state() == State::Jog) CHECK(released);      // never starts from a held JOG
        // one direction never runs longer than the jam timeout, plus the step
        bool on = out.extend || out.retract;
        if (!on || out.extend != prev.extend || out.retract != prev.retract) same_since = now;
        CHECK(!on || now - same_since <= jam_ms);

        if (c.state() != State::Idle) released = false;
        if (!in.jog) released = true;
        prev_state = c.state();
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
    {  // E-STOP: valves off, idle after the reset until button A
        Rig r;
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
        r.press_start();
        r.run(20);
        r.pos = 40;  // the rod sticks
        for (int i = 0; i < 100; ++i) {
            r.in.home = false;
            r.in.front = false;
            r.out = r.c.step(r.in, r.now);
            r.now += 10;
        }
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
        r.press_start();
        for (int i = 0; i < 100; ++i) {  // valve on, rod does not leave home
            r.in.home = true;
            r.in.front = false;
            r.out = r.c.step(r.in, r.now);
            r.now += 10;
        }
        CHECK(r.c.fault() == Fault::Jam);
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
    {  // starting mid-stroke retracts first
        Rig r;
        r.pos = 50;
        r.press_start();
        CHECK(r.out.retract && !r.out.extend);
    }
    for (uint32_t seed : {1u, 2u, 3u, 12345u}) random_run(seed, 800);
    std::puts("ok");
    return 0;
}
