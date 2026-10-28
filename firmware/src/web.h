// Wi-Fi: an access point that always runs, the home network when set, the status and settings page, OTA.
#pragma once
#include <Arduino.h>
#include <Preferences.h>

#include "logic.h"

void web_begin(autolever::Controller& press, Preferences& prefs);
void web_loop(bool idle);   // OTA is open only while the press is idle

String web_ap_ssid();
String web_ap_password();
String web_ip();            // address on the home network, "-" while not connected
