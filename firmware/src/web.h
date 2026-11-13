// Wi-Fi: an access point that always runs, the home network when set, the status and settings page, OTA.
#pragma once
#include <Arduino.h>
#include <Preferences.h>

#include <mutex>

#include "logic.h"

// The page is served in its own task, so a slow or stalled client never holds up loop(). The page reads and
// changes the press only while it holds lock; loop() takes it for the same.
void web_begin(autolever::Controller& press, Preferences& prefs, std::mutex& lock);
// OTA, open only while the press is idle; an upload starts only in a loop whose readback read every relay off.
void web_loop(bool idle, bool relays_off);

String web_ap_ssid();
String web_ap_password();
String web_ip();            // address on the home network, "-" while not connected
