// Relay rule of the bench image, free of hardware calls so tests/test_firmware.py can run it natively.
#pragma once

#include <cstdint>

namespace bench {

constexpr uint32_t RELAY_ON_MS = 10000;   // the bench image never holds a valve on longer than this

struct Relays {
    bool on[4] = {};
    uint32_t since[4] = {};

    // toggle: the relays whose button was pressed in this loop. rails_ok: inputs 3 and 4 are both on (E-STOP
    // released, pressure fine); while either is off every relay stays off, so none is latched when the rail returns.
    void step(const bool (&toggle)[4], bool all_off, bool rails_ok, uint32_t now) {
        for (int i = 0; i < 4; ++i) {
            if (toggle[i]) {
                on[i] = !on[i];
                since[i] = now;
            }
            if (all_off || !rails_ok || now - since[i] >= RELAY_ON_MS) on[i] = false;
        }
    }
};

}  // namespace bench
