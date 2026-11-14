// Relay rule of the bench image, free of hardware calls so tests/test_firmware.py can run it natively.
#pragma once

#include <cstdint>

namespace bench {

constexpr uint32_t RELAY_ON_MS = 10000;   // the bench image never holds a valve on longer than this
constexpr uint32_t LOCKOUT_MS = 1000;     // presses ignored after the automatic off, so a late "off" press stays off

struct Relays {
    bool on[4] = {};
    uint32_t since[4] = {};
    bool locked = false;
    uint32_t locked_at = 0;

    // toggle: the relays whose button was pressed in this loop. all_off: A and C held. estop_ok, pressure_ok: inputs 3
    // and 4; while either is off every relay stays off, so none is latched when the rail returns. The first relay to
    // reach RELAY_ON_MS switches every relay off: relay 1 NC feeds relay 2 COM, so relay 1 alone going off would put
    // Y2 on with no button pressed.
    void step(const bool (&toggle)[4], bool all_off, bool estop_ok, bool pressure_ok, uint32_t now) {
        if (locked && now - locked_at >= LOCKOUT_MS) locked = false;
        // Checked before the toggles, so a press on the expiring relay cannot leave the others on.
        bool timed_out = false;
        for (int i = 0; i < 4; ++i) {
            if (on[i] && now - since[i] >= RELAY_ON_MS) timed_out = true;
        }
        if (timed_out) {
            locked = true;
            locked_at = now;
        }
        for (int i = 0; i < 4; ++i) {
            if (toggle[i] && !locked) {
                on[i] = !on[i];
                since[i] = now;
            }
        }
        if (timed_out || all_off || !estop_ok || !pressure_ok) {
            for (bool& o : on) o = false;
        }
    }

    // read(i), write(i, on): the relay outputs. Off from relay 4 down, then on from relay 1 up (src/main.cpp also writes
    // the off first): relay 2 opens before relay 1 NC feeds its COM, and relay 1 cuts that feed before relay 2 closes.
    template <class Read, class Write>
    void sync(Read read, Write write) const {
        for (int i = 3; i >= 0; --i) {
            if (!on[i] && read(i)) write(i, false);
        }
        for (int i = 0; i < 4; ++i) {
            if (on[i] && !read(i)) write(i, true);
        }
    }
};

}  // namespace bench
