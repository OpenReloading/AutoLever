// Press logic with no hardware calls, so it runs in the native test (tests/test_firmware.py).
#pragma once
#include <cstdint>

namespace autolever {

struct Inputs {
    bool home;         // B0: rod fully home
    bool front;        // B1: rod at the front end
    bool estop_ok;     // valve rail is live after the E-STOP
    bool pressure_ok;  // valve rail is live after the pressure switch
    bool start;        // button A
    bool jog;          // button B
};

struct Outputs {
    bool extend;   // valve Y1
    bool retract;  // valve Y2
};

enum class State { Idle, Auto, Jog, Fault };
enum class Fault { None, EStop, Pressure, Sensor, Jam };

const char* state_name(State s);
const char* fault_name(Fault f);   // empty for Fault::None

// Settings page value in seconds to the jam timeout, kept between 2 and 120 s.
inline uint32_t jam_ms_from_seconds(long s) { return (uint32_t)(s < 2 ? 2 : s > 120 ? 120 : s) * 1000u; }

// Settings form field to the jam timeout through jam_ms_from_seconds; false for an empty or non-numeric field.
bool jam_ms_from_text(const char* text, uint32_t& ms);

// Origin or Referer header of a settings post against the Host header: true when the source is
// empty or names that host (scheme and path ignored, case-insensitive).
bool same_origin(const char* source, const char* host);

// Wi-Fi form password: true when empty (keeps the stored one) or 8 to 63 characters (WPA2 passphrase).
bool wifi_pass_ok(const char* pass);

class Controller {
public:
    // Longest time for one stroke (out or back); longer is a jam.
    uint32_t jam_ms = 15000;

    Outputs step(const Inputs& in, uint32_t now_ms);

    State state() const { return state_; }
    Fault fault() const { return fault_; }
    bool stopping() const { return stopping_; }
    uint32_t cycles() const { return cycles_; }
    void set_cycles(uint32_t n) { cycles_ = n; }

private:
    enum class Phase { Extend, Retract };

    void enter_fault(Fault f);
    void begin(State s, const Inputs& in, uint32_t now_ms);

    State state_ = State::Idle;
    Fault fault_ = Fault::None;
    Fault latched_ = Fault::None;  // jam or sensor fault under a supply fault, shown again once the rail is back
    Phase phase_ = Phase::Extend;
    uint32_t phase_since_ = 0;
    uint32_t cycles_ = 0;
    bool prev_start_ = false;
    bool armed_ = false;  // JOG was seen released since the last stop; a held JOG never starts the press
    bool stopping_ = false;
    bool reached_front_ = false;
};

}  // namespace autolever
