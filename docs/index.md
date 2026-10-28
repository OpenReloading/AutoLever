---
title: Introduction
hide: [navigation]
---

# AutoLever: pneumatic drive for the Lee APP

!!! danger "Safety"

    --8<-- "safety.md"

!!! warning "Pre-release, October 2026"

    Nothing has been built yet, the printed parts are not on MakerWorld yet, details will change. The StamPLC firmware and wiring have passed their automated tests only; the bench check on the real unit is still open.

Give your Lee APP an air-powered upgrade. AutoLever takes over the lever work for sizing and decapping. Press START and a Festo cylinder keeps it cycling, stroke after stroke. Press START again when you’re done.

[Start with the BOM](bom.md){ .md-button .md-button--primary }

- **One controller, two sensors.** An M5Stack StamPLC runs the sequence.
- **Open firmware.** Flash it once over USB-C with PlatformIO; later updates go over Wi-Fi.
- **Free plans.** Bring your press and build your own.

Built by reloaders for reloaders, with AI as a tool.

!!! note "Relay edition (deprecated prototype)"

    The first prototype used four relays and a timer. Its guide stays as the [relay edition](relay.md) until the parts are removed; do not start a new build from it.

## What it does

- **Automatic cycling.** Press START once for continuous out-and-back strokes. Press it again to stop after the current stroke.
- **JOG control.** With automatic mode off, hold JOG to cycle. Release it to stop.
- **Free at rest.** The cylinder vents when the valve is off, so you can move the lever by hand.
- **Cycle monitoring.** A stroke that takes longer than the jam time (15 s, set between 2 and 120 s on the web page) ends automatic mode. Both sensors on at once is a sensor fault.
- **Pressure trip.** The pressure switch cuts power to the valves at 6 bar.
- **Cycle counter.** The display and the web page show the cycles, kept across power-off.
- **Web page.** The StamPLC opens its own Wi-Fi and joins your home network; the page shows the state and sets the jam time. Password and address are on the info screen.
- **24 V throughout.** An enclosed external power supply powers the controls.

## At the controls

POWER on. The three buttons under the display: A starts and stops automatic cycling, B jogs while held, C shows the info screen. E-STOP cuts the power to the valves (the StamPLC stays on and shows the fault); twist to release. A supply fault clears itself when the power is back; after a jam or a sensor fault, press A.

Release JOG after any stop or trip. A held JOG never starts the press; release it and press it again.

Check the printed handle adapter for cracks before each session.

## What you’ll need

- A Lee APP (Classic preferred; Deluxe also works).
- A compressed-air supply at 7–10 bar.
- The BOM parts, plus a printed handle adapter, control box and yellow E-STOP ring, and a computer with [PlatformIO](https://platformio.org/) to flash the StamPLC (project folder `firmware/` in the repository).

## Print it

PETG or ASA. Handle adapter: 6 walls and 40% infill. Control box: 15–20% infill. The base and lid fit on a 256 mm bed. Print the E-STOP ring in yellow.

## Build it

1. Print the parts and gather the components from the [BOM](bom.md).
2. Mount the press, cylinder, valve and filter-regulator on a board. Clamp the handle adapter onto the press lever.
3. Follow the [Wiring](wiring.md) and [Tubing](tubing.md) guides to connect everything.
4. Flash the bench image (`pio run -e bench -t upload` in `firmware/`): it shows all eight inputs live and toggles the relays. Set the sensors with air disconnected: POWER on, move the rod by hand. Then flash the press firmware (`pio run -e stamplc -t upload`) and test with air at 2 bar using JOG before trying START.
