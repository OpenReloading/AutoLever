// Native test of the bench image's relay rule; built and run by tests/test_firmware.py.
#include <cstdio>
#include <cstdlib>

#include "../bench/relays.h"

#define CHECK(c)                                                         \
    do {                                                                 \
        if (!(c)) {                                                      \
            std::printf("FAIL line %d: %s\n", __LINE__, #c);             \
            std::exit(1);                                                \
        }                                                                \
    } while (0)

static const bool NONE[4] = {false, false, false, false};
static const bool ABC[4] = {true, true, true, false};

static bool any_on(const bench::Relays& r) { return r.on[0] || r.on[1] || r.on[2] || r.on[3]; }

int main() {
    const bool a[4] = {true, false, false, false};
    const bool b[4] = {false, true, false, false};
    // every relay switches off by itself 10 s after it was switched on
    {
        bench::Relays r;
        r.step(ABC, false, true, true, 5000);
        CHECK(r.on[0] && r.on[1] && r.on[2]);
        r.step(NONE, false, true, true, 14999);
        CHECK(r.on[0] && r.on[1] && r.on[2]);
        r.step(NONE, false, true, true, 15000);
        CHECK(!any_on(r));
    }
    // the first relay to reach 10 s switches every relay off (relay 1 off alone would put Y2 on), also across the
    // millis() wrap
    {
        bench::Relays r;
        r.step(a, false, true, true, 0xFFFFF000u);
        r.step(b, false, true, true, 0xFFFFF000u + 1000);
        r.step(NONE, false, true, true, 0xFFFFF000u + 9999);
        CHECK(r.on[0] && r.on[1]);
        r.step(NONE, false, true, true, 0xFFFFF000u + 10000);
        CHECK(!any_on(r));
    }
    // a second press switches the relay off, a third switches it on for a fresh 10 s
    {
        bench::Relays r;
        r.step(a, false, true, true, 1000);
        CHECK(r.on[0]);
        r.step(a, false, true, true, 2000);
        CHECK(!r.on[0]);
        r.step(a, false, true, true, 3000);
        r.step(NONE, false, true, true, 12999);
        CHECK(r.on[0]);
        r.step(NONE, false, true, true, 13000);
        CHECK(!any_on(r));
    }
    // presses are ignored for 1 s after the automatic off
    {
        bench::Relays r;
        r.step(a, false, true, true, 0);
        r.step(NONE, false, true, true, 10000);
        CHECK(!any_on(r));
        r.step(a, false, true, true, 10050);
        CHECK(!any_on(r));
        r.step(a, false, true, true, 10999);
        CHECK(!any_on(r));
        r.step(a, false, true, true, 11000);
        CHECK(r.on[0]);
    }
    // input 3 or 4 off, each alone: every relay off at once, none can be switched on, none comes back with the rail
    for (int off = 0; off < 2; ++off) {
        const bool estop_ok = off != 0, pressure_ok = off != 1;
        bench::Relays r;
        r.step(ABC, false, true, true, 1000);
        r.step(NONE, false, estop_ok, pressure_ok, 1010);
        CHECK(!any_on(r));
        r.step(ABC, false, estop_ok, pressure_ok, 1020);
        CHECK(!any_on(r));
        r.step(NONE, false, true, true, 1030);
        CHECK(!any_on(r));
    }
    // holding A and C switches everything off
    {
        bench::Relays r;
        r.step(ABC, false, true, true, 1000);
        r.step(NONE, true, true, true, 1010);
        CHECK(!any_on(r));
    }
    // a press on relay 1 as it reaches 10 s still switches every relay off and starts the lockout
    {
        bench::Relays r;
        r.step(a, false, true, true, 1000);
        r.step(b, false, true, true, 6000);
        r.step(a, false, true, true, 11000);
        CHECK(!any_on(r));
        r.step(a, false, true, true, 11500);
        CHECK(!any_on(r));
    }
    // relays switch off from relay 4 down, then on from relay 1 up: relay 1 never feeds a closed relay 2 COM
    {
        bench::Relays r;
        bool out[4] = {false, true, true, false};
        r.on[0] = true;
        r.on[3] = true;
        int order[4], n = 0;
        r.sync([&](int i) { return out[i]; },
               [&](int i, bool v) {
                   out[i] = v;
                   order[n++] = v ? i + 1 : -(i + 1);
               });
        CHECK(n == 4);
        CHECK(order[0] == -3 && order[1] == -2 && order[2] == 1 && order[3] == 4);
        CHECK(out[0] && !out[1] && !out[2] && out[3]);
    }
    std::printf("ok\n");
    return 0;
}
