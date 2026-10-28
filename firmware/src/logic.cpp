#include "logic.h"

#include <cctype>
#include <cstring>

namespace autolever {

const char* state_name(State s) {
    switch (s) {
        case State::Idle: return "IDLE";
        case State::Auto: return "AUTO";
        case State::Jog: return "JOG";
        default: return "FAULT";
    }
}

const char* fault_name(Fault f) {
    switch (f) {
        case Fault::EStop: return "E-STOP";
        case Fault::Pressure: return "PRESSURE";
        case Fault::Sensor: return "SENSOR";
        case Fault::Jam: return "JAM";
        default: return "";
    }
}

void Controller::enter_fault(Fault f) {
    state_ = State::Fault;
    fault_ = f;
    armed_ = false;
    stopping_ = false;
}

void Controller::begin(State s, const Inputs& in, uint32_t now_ms) {
    state_ = s;
    armed_ = false;
    stopping_ = false;
    reached_front_ = false;
    // Mid-stroke: go home first.
    phase_ = in.home ? Phase::Extend : Phase::Retract;
    phase_since_ = now_ms;
}

Outputs Controller::step(const Inputs& in, uint32_t now_ms) {
    bool start_edge = in.start && !prev_start_;
    prev_start_ = in.start;

    Fault f = !in.estop_ok       ? Fault::EStop
              : !in.pressure_ok  ? Fault::Pressure
              : (in.home && in.front) ? Fault::Sensor
                                  : Fault::None;
    if (f != Fault::None) {
        enter_fault(f);
        return {};
    }

    if (state_ == State::Fault) {
        // Supply faults clear themselves once the rail is back; a jam or a sensor fault waits for button A.
        bool supply = fault_ == Fault::EStop || fault_ == Fault::Pressure;
        if (!supply && !start_edge) return {};
        state_ = State::Idle;
        fault_ = Fault::None;
        start_edge = false;
    }

    if (state_ == State::Idle) {
        if (!in.jog) armed_ = true;
        if (start_edge) {
            begin(State::Auto, in, now_ms);
            start_edge = false;  // the press that started it is not a stop request
        } else if (in.jog && armed_) {
            begin(State::Jog, in, now_ms);
        } else {
            return {};
        }
    }

    if (state_ == State::Jog && !in.jog) {
        state_ = State::Idle;
        return {};
    }
    if (state_ == State::Auto && start_edge) stopping_ = true;

    if (phase_ == Phase::Extend && in.front) {
        reached_front_ = true;
        phase_ = Phase::Retract;
        phase_since_ = now_ms;
    } else if (phase_ == Phase::Retract && in.home) {
        if (reached_front_) ++cycles_;
        reached_front_ = false;
        if (stopping_) {
            state_ = State::Idle;
            stopping_ = false;
            return {};
        }
        phase_ = Phase::Extend;
        phase_since_ = now_ms;
    }

    if (now_ms - phase_since_ > jam_ms) {
        enter_fault(Fault::Jam);
        return {};
    }
    return {phase_ == Phase::Extend, phase_ == Phase::Retract};
}

bool same_origin(const char* source, const char* host) {
    if (!*source) return true;
    const char* sep = std::strstr(source, "://");
    if (sep) source = sep + 3;
    for (; *source && *source != '/'; ++source, ++host)
        if (std::tolower((unsigned char)*source) != std::tolower((unsigned char)*host)) return false;
    return !*host;
}

}  // namespace autolever
