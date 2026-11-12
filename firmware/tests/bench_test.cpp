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
    // every relay switches off by itself 10 s after it was switched on
    {
        bench::Relays r;
        r.step(ABC, false, true, 5000);
        CHECK(r.on[0] && r.on[1] && r.on[2]);
        r.step(NONE, false, true, 14999);
        CHECK(r.on[0] && r.on[1] && r.on[2]);
        r.step(NONE, false, true, 15000);
        CHECK(!any_on(r));
    }
    // the time runs per relay, from its own switch-on, also across the millis() wrap
    {
        bench::Relays r;
        const bool a[4] = {true, false, false, false};
        const bool b[4] = {false, true, false, false};
        r.step(a, false, true, 0xFFFFF000u);
        r.step(b, false, true, 0xFFFFF000u + 4000);
        r.step(NONE, false, true, 0xFFFFF000u + 10000);
        CHECK(!r.on[0] && r.on[1]);
        r.step(NONE, false, true, 0xFFFFF000u + 14000);
        CHECK(!any_on(r));
    }
    // input 3 or 4 off: every relay off at once, none can be switched on, none comes back with the rail
    {
        bench::Relays r;
        r.step(ABC, false, true, 1000);
        r.step(NONE, false, false, 1010);
        CHECK(!any_on(r));
        r.step(ABC, false, false, 1020);
        CHECK(!any_on(r));
        r.step(NONE, false, true, 1030);
        CHECK(!any_on(r));
    }
    // holding A and C switches everything off
    {
        bench::Relays r;
        r.step(ABC, false, true, 1000);
        r.step(NONE, true, true, 1010);
        CHECK(!any_on(r));
    }
    std::printf("ok\n");
    return 0;
}
