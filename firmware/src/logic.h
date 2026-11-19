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
    bool buttons_ok;   // start and jog come from a good read; false: both are unknown
};

struct Outputs {
    bool extend;   // valve Y1
    bool retract;  // valve Y2
    bool enable;   // relay 3, the feed of relays 1 and 2: on only while a stroke is commanded
};

constexpr uint8_t RELAY_EXTEND = 0, RELAY_RETRACT = 1, RELAY_ENABLE = 2;   // relays 1, 2 and 3

// Writes out through write(relay, on). Relay 3 feeds relays 1 and 2 (wiring step E): it opens first and closes last,
// so a stuck relay 1 or 2 loses its feed on every fault and at idle. Of relays 1 and 2 the one that turns off is
// written first, so extend and retract are never on together.
template <class Write>
void write_relays(const Outputs& out, Write write) {
    if (!out.enable) write(RELAY_ENABLE, false);
    if (out.extend) {
        write(RELAY_RETRACT, out.retract);
        write(RELAY_EXTEND, true);
    } else {
        write(RELAY_EXTEND, false);
        write(RELAY_RETRACT, out.retract);
    }
    if (out.enable) write(RELAY_ENABLE, true);
}

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
    // In IDLE a START press starts AUTO only after good reads showed START released for this long in a row.
    // A failed button read (buttons_ok false) is neither a press nor a release: it ends that run, disarms JOG,
    // stops a JOG and acknowledges no fault.
    static constexpr uint32_t start_release_ms = 150;

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
    bool prev_start_ = true;  // a START held at power-up is not a press
    uint32_t released_since_ = 0;  // first step of the current or last run of released START reads
    uint32_t released_ms_ = 0;     // length of that run, up to its last released read
    bool armed_ = false;  // JOG was seen released since the last stop; a held JOG never starts the press
    bool stopping_ = false;
    bool reached_front_ = false;
};

// START and JOG from the input status register of the button expander (PI4IOE5V6408 at 0x43). Each button pulls its
// pin low against the expander's pull-up, so a pressed button reads 0: A (START) is pin 2, B (JOG) pin 1.
constexpr uint8_t BUTTON_REGISTER = 0x0F;
constexpr uint8_t BUTTON_START_BIT = 1u << 2, BUTTON_JOG_BIT = 1u << 1;

// Debounces the register reads: a button's new level counts once good reads have shown it for debounce_ms with
// no failed read in between. A failed read makes both levels unknown until good reads settle them again.
class Buttons {
public:
    static constexpr uint32_t debounce_ms = 10;

    struct Levels {
        bool ok;     // both levels are settled and the last read was good
        bool start;  // pressed
        bool jog;    // pressed
    };

    // read_ok: the read of BUTTON_REGISTER was acknowledged; reg is its value, ignored when read_ok is false.
    Levels step(bool read_ok, uint8_t reg, uint32_t now_ms);

private:
    struct Contact {
        bool settled = false;  // pressed holds a debounced level
        bool pressed = false;
        bool seen = false;     // run_pressed holds the level of the last good read
        bool run_pressed = false;
        uint32_t run_since = 0;  // first good read of the current run of equal reads

        void read(bool now_pressed, uint32_t now_ms);
        void fail() { settled = seen = false; }
    };

    Contact start_, jog_;
};

// Relay readback after each write, one bit per relay. A failed read reads as all off in the library, so it counts too.
class RelayCheck {
public:
    // True once the read failed, or a relay commanded off read on, in every call for more than 100 ms.
    bool stuck(bool read_ok, uint8_t read, uint8_t commanded, uint32_t now_ms);

private:
    bool bad_ = false;
    uint32_t bad_since_ = 0;
};

// Over-the-air updates: closed until button C is held, then open for 10 minutes.
class UpdateWindow {
public:
    void open(uint32_t now_ms);
    // Called in every loop: once closed it stays closed until the next open(), also across the millis() wrap.
    bool is_open(uint32_t now_ms);

private:
    bool open_ = false;
    uint32_t since_ = 0;
};

}  // namespace autolever
