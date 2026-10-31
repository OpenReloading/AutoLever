#include "web.h"

#include <ArduinoOTA.h>
#include <ESPmDNS.h>
#include <WebServer.h>
#include <WiFi.h>

using namespace autolever;

static WebServer server(80);
static Controller* press = nullptr;
static Preferences* prefs = nullptr;
static std::mutex* lock = nullptr;
static String ap_ssid, ap_pass;
static bool ota_open = false;

static const char PAGE[] PROGMEM = R"html(<!doctype html><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>AutoLever</title>
<style>body{font:16px system-ui;margin:1rem auto;max-width:28rem;padding:0 1rem}
h1{font-size:2rem;margin:.2em 0}form{margin:1.2rem 0}label{display:block;margin:.4rem 0}
input{font:inherit;padding:.3rem;width:100%;box-sizing:border-box}button{font:inherit;padding:.4rem .8rem;margin-top:.4rem}
.f{color:#b00020;font-weight:600;min-height:1.4em}small{color:#555}</style>
<h1 id=s>...</h1><div class=f id=f></div><p>Cycles <b id=c>-</b></p>
<form method=post action=/settings><label>Jam timeout, seconds per stroke (2 to 120)
<input name=jam type=number min=2 max=120 value=%JAM%></label><button>Save</button></form>
<form method=post action=/counter onsubmit="return confirm('Reset the cycle counter?')"><button>Reset counter</button></form>
<form method=post action=/wifi><label>Home network<input name=ssid value="%SSID%"></label>
<label>Password<input name=pass type=password></label><button>Save and connect</button></form>
<small>Changes ask for the user admin and the device password shown on the box (info screen).</small>
<script>async function u(){try{const r=await(await fetch('/status')).json();
s.textContent=r.state;f.textContent=r.fault;c.textContent=r.cycles}catch(e){s.textContent='no connection'}}
u();setInterval(u,1000)</script>)html";

static String esc(const String& in) {
    String out;
    for (char ch : in) {
        switch (ch) {
            case '&': out += "&amp;"; break;
            case '<': out += "&lt;"; break;
            case '>': out += "&gt;"; break;
            case '"': out += "&quot;"; break;
            default: out += ch;
        }
    }
    return out;
}

// Settings posts only from this device's own page: the browser sends saved Basic credentials with a form from any site.
static bool authed() {
    String from = server.hasHeader("Origin") ? server.header("Origin") : server.header("Referer");
    if (!same_origin(from.c_str(), server.hostHeader().c_str())) {
        server.send(403, "text/plain", "Changes only from this device's own page");
        return false;
    }
    if (server.authenticate("admin", ap_pass.c_str())) return true;
    server.requestAuthentication();
    return false;
}

static void see_other() {
    server.sendHeader("Location", "/");
    server.send(303);
}

// Handlers hold the lock only around the press and the preferences: a send can wait seconds on a slow client.
static void handle_root() {
    String page = FPSTR(PAGE);
    {
        std::lock_guard<std::mutex> hold(*lock);
        page.replace("%JAM%", String(press->jam_ms / 1000));
        page.replace("%SSID%", esc(prefs->getString("ssid", "")));
    }
    server.send(200, "text/html", page);
}

static void handle_status() {
    char json[128];
    std::unique_lock<std::mutex> hold(*lock);
    snprintf(json, sizeof json, "{\"state\":\"%s\",\"fault\":\"%s\",\"cycles\":%lu,\"jam_s\":%lu}",
             state_name(press->state()), fault_name(press->fault()), (unsigned long)press->cycles(),
             (unsigned long)(press->jam_ms / 1000));
    hold.unlock();
    server.send(200, "application/json", json);
}

static void handle_settings() {
    if (!authed()) return;
    uint32_t ms;
    if (!jam_ms_from_text(server.arg("jam").c_str(), ms)) {
        server.send(400, "text/plain", "Jam timeout must be a whole number of seconds");
        return;
    }
    {
        std::lock_guard<std::mutex> hold(*lock);
        press->jam_ms = ms;
        prefs->putUInt("jam_ms", press->jam_ms);
    }
    see_other();
}

static void handle_counter() {
    if (!authed()) return;
    {
        std::lock_guard<std::mutex> hold(*lock);
        press->set_cycles(0);   // main.cpp saves a changed count
    }
    see_other();
}

static void handle_wifi() {
    if (!authed()) return;
    String ssid = server.arg("ssid");
    if (ssid.length() == 0 || ssid.length() > 32) {
        server.send(400, "text/plain", "Network name must be 1 to 32 characters");
        return;
    }
    if (!wifi_pass_ok(server.arg("pass").c_str())) {
        server.send(400, "text/plain", "Password must be 8 to 63 characters");
        return;
    }
    String pass = server.arg("pass");
    {
        std::lock_guard<std::mutex> hold(*lock);
        prefs->putString("ssid", ssid);
        if (pass.length()) prefs->putString("wpass", pass);   // empty keeps the stored password
        else pass = prefs->getString("wpass", "");
    }
    WiFi.disconnect(false);
    WiFi.begin(ssid.c_str(), pass.c_str());
    see_other();
}

static void serve(void*) {
    for (;;) {
        server.handleClient();
        delay(1);
    }
}

void web_begin(Controller& c, Preferences& p, std::mutex& l) {
    press = &c;
    prefs = &p;
    lock = &l;

    WiFi.mode(WIFI_AP_STA);   // before the MAC is read
    ap_ssid = "AutoLever-" + WiFi.macAddress().substring(12);
    ap_ssid.replace(":", "");
    ap_pass = prefs->getString("ap_pass", "");
    if (ap_pass.length() < 8) {
        static const char alphabet[] = "abcdefghjkmnpqrstuvwxyz23456789";   // no look-alikes
        ap_pass = "";
        for (int i = 0; i < 10; ++i) ap_pass += alphabet[esp_random() % (sizeof alphabet - 1)];
        prefs->putString("ap_pass", ap_pass);
    }

    WiFi.softAP(ap_ssid.c_str(), ap_pass.c_str());
    WiFi.setAutoReconnect(true);
    String ssid = prefs->getString("ssid", "");
    if (ssid.length()) WiFi.begin(ssid.c_str(), prefs->getString("wpass", "").c_str());

    MDNS.begin("autolever");
    MDNS.addService("http", "tcp", 80);
    server.on("/", HTTP_GET, handle_root);
    server.on("/status", HTTP_GET, handle_status);
    server.on("/settings", HTTP_POST, handle_settings);
    server.on("/counter", HTTP_POST, handle_counter);
    server.on("/wifi", HTTP_POST, handle_wifi);
    static const char* headers[] = {"Origin", "Referer"};
    server.collectHeaders(headers, 2);
    server.begin();
    // On the other core than loop(), at the idle priority: a request parse polls without yielding, and the idle task
    // of that core must still run within the task watchdog timeout.
    xTaskCreatePinnedToCore(serve, "web", 8192, nullptr, tskIDLE_PRIORITY, nullptr, 0);

    ArduinoOTA.setHostname("autolever");
    ArduinoOTA.setPassword(ap_pass.c_str());
}

void web_loop(bool idle) {
    if (idle != ota_open) {
        if (idle) ArduinoOTA.begin();
        else ArduinoOTA.end();
        ota_open = idle;
    }
    if (ota_open) ArduinoOTA.handle();
}

String web_ap_ssid() { return ap_ssid; }
String web_ap_password() { return ap_pass; }
String web_ip() { return WiFi.status() == WL_CONNECTED ? WiFi.localIP().toString() : String("-"); }
