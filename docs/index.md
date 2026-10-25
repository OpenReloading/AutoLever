---
title: Introduction
hide: [navigation]
---

# AutoLever: pneumatic drive for the Lee APP

!!! danger "Safety"

    --8<-- "safety.md"

Give your Lee APP an air-powered upgrade. AutoLever takes over the lever work for sizing and decapping. Press START and a Festo cylinder keeps it cycling, stroke after stroke. Press STOP when you’re done.

[Start with the BOM](bom.md){ .md-button .md-button--primary }

- **Four relays, two sensors.** They run the sequence.
- **No code.** Nothing to flash and no controller to program.
- **Free plans.** Bring your press and build your own.

Built by reloaders for reloaders, with AI as a tool.

## What it does

- **Automatic cycling.** Press START once for continuous out-and-back strokes. Press STOP to stop and vent the cylinder.
- **JOG control.** With automatic mode off, hold JOG to cycle. Release it to stop. STOP interrupts JOG too.
- **Free at rest.** The cylinder vents when the valve is off, so you can move the lever by hand.
- **Cycle monitoring.** A timeout ends automatic mode and interrupts JOG. The timer resets at home, so it cannot detect a stall there.
- **Pressure trip.** The pressure switch cuts power to the valves, sensors and relays at 6 bar.
- **24 V throughout.** An enclosed external power supply powers the controls.

## At the controls

POWER on, START to run, STOP to stop. E-STOP cuts all control power; twist to release. Clear the fault before pressing START to resume automatic cycling.

Release JOG after any stop or trip. If you keep it held, the press can restart when STOP is released or the trip clears.

Check the printed handle adapter for cracks before each session.

## What you’ll need

- A Lee APP (Classic preferred; Deluxe also works).
- A compressed-air supply at 7–10 bar.
- The BOM parts, plus a printed handle adapter, control box and yellow E-STOP ring.

## Print it

PETG or ASA. Handle adapter: 6 walls and 40% infill. Control box: 15–20% infill. The base, lid and console plate fit on a 256 mm bed. Print the E-STOP ring in yellow.

## Build it

1. Print the parts and gather the components from the [BOM](bom.md).
2. Mount the press, cylinder, valve and filter-regulator on a board. Clamp the handle adapter onto the press lever.
3. Follow the [Wiring](wiring.md) and [Tubing](tubing.md) guides to connect everything.
4. Set the sensors with air disconnected: POWER on, move the rod by hand. Test with air at 2 bar using JOG before trying START.
