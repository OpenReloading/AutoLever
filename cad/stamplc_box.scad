// Control box for the StamPLC variant: the StamPLC (M5Stack K141) on a short DIN rail, 24 V DC only.
//   Lid:   the whole front of the StamPLC (display, buttons A B C, RESET/BOOT, both HY2.0 ports, the screw
//          terminals) sits flush in a window, so every control and the wiring stay reachable with the lid on.
//          E-STOP (22 mm, on a yellow ring) at the left. A notch on the USB-C side takes the plug; the usb_plug
//          part fills it when no cable is attached.
//   Left wall: POWER (Ø20 snap-in rocker). Right wall at the back: DC jack. Back wall: ONE oval opening for the
//          whole cable bundle (valve, pressure switch, both sensors) with two tie slots beside it.
//   Front wall: a clip rack for five Wago 221 connectors (3 x 221-415, 2 x 221-413), each standing on edge, wire
//          entries up, levers towards the unit, close to the relay terminals of the StamPLC.
// No mains inside; the supply stays outside and plugs into the jack.
//
// Coordinates: X along the width, Y = 0 is the operator face, Z up, origin = outer front-left-bottom corner.
// Unit frame (StamPLC, from the M5Stack structure file): origin on the DIN rail line in the middle of the width,
// x across, y up the front face (inputs row up, relay row down), z out of the front plane (0 = front face).
//
// Print: PETG or ASA, 4 perimeters, 15-20 % infill, no supports. Base upright, lid face down, ring flat in yellow.
// Hardware: 4 x M3x8 + 4 x M3 heat-set inserts (lid), 2 x M3x6 pan-head + 2 inserts (rail), 35 mm DIN rail cut to
//           100 mm (slot centres 12.5 and 87.5 from its end), 4 cable ties.
// Fit order: base -> inserts, rail, jack, rocker -> StamPLC onto the rail -> wire -> lid over the unit.
// Test fit the base with the unit before printing the lid: rail_gap and plc_depth set the height of the unit.

part = "assembly";        // "base" | "lid" | "estop_ring" | "usb_plug" | "assembly" | "exploded"
wood_screw_holes = false; // true: 4 countersunk holes in the floor for 4 mm wood screws
$fn = 48;

// ---- StamPLC K141 ----
plc_w     = 72;           // width; the front part (10 mm deep) is 72 x 77, the body behind it 72 x 72
plc_y     = [-39, 38];    // y extent of the front part
plc_depth = 30.7;         // front face to the back of the DIN clip
rail_gap  = 1;            // back of the unit to the surface of the rail (side view of the data sheet drawing)
plc_play  = 0.3;          // window play per side
usb_y     = 11;           // centre of the USB-C opening on the +x side (read from the 3D file, +-1 mm)
usb_notch = [26, 16];     // lid notch for the plug: length beyond the window, width

// ---- bought parts ----
hole_d       = 22.4;      // 22 mm operators
estop_ring   = [56, 1.5]; // yellow ring under the E-STOP bezel, diameter and thickness
estop_depth  = 58;        // E-STOP with its contact blocks behind the panel
rocker_d     = 20.2;      // POWER, round snap-in rocker
rocker_panel = 2;         // its clips want a thin panel: the wall is thinned to this from inside
rocker_recess = 28;
jack_d       = 8.2;       // panel DC jack, 5.5 x 2.1 mm
rail_w       = 35;
rail_h       = 7.5;
rail_len     = 100;
rail_slots   = [12.5, 87.5];
insert_d     = 4.2;       // M3 heat-set insert; 2.6 for self-tapping M3
insert_h     = 6;
screw_d      = 3.4;
wood_d       = 4.5;
wood_head    = 9;

// ---- box ----
t        = 2.6;
floor_t  = 3;
lid_t    = 3;
r_out    = 3;
boss_r   = 4.5;
fm       = 24;            // free space in front of the unit (relay wires turn here)
bm       = 26;            // behind it (input wires)
x_left   = 70;            // window left edge in the cavity: the E-STOP ring takes 4 .. 60
right_room = 34;          // beside the window on the USB-C side
exit_d   = [30, 14];      // cable opening, width x height
exit_z   = 36;
jack_z   = 33;
rocker_z = 33;
rocker_y = 30;            // on the left wall, cavity y

// Wago 221 rack on the front wall, left to right: 24 V, 0 V, 0 V, E-STOP out, valve rail. The snap arms hold the
// connector by the rim of its lever face; widths and heights as measured on the real parts (see the relay box).
wagos     = [29.7, 29.7, 29.7, 18.5, 18.5];
wago_h    = [8.4, 8.4, 8.4, 8.3, 8.3];   // housing height = ledge depth from the wall
arm_t     = 1.4;
arm_h     = 16;
lip       = 0.8;
wago_grip = 0.5;
slot_gap  = 1;
rack_z    = 20;           // underside of the connectors; the entries end at 38, 25 mm below the lid
rack_x0   = 12;           // right of the corner column; the POWER rocker sits behind it on the left wall (y 20 to 40)

win  = [plc_w + 2 * plc_play, plc_y[1] - plc_y[0] + 2 * plc_play];
cx   = x_left + win.x + right_room;
cy   = fm + win.y + bm;
inner_h = estop_depth + 2;
H    = floor_t + inner_h;   // rim height; the lid sits on top
Hz   = H + lid_t;           // front plane of the unit
W    = cx + 2 * t;
D    = cy + 2 * t;
ox   = x_left + plc_play + plc_w / 2;          // unit origin in the cavity
oy   = fm + plc_play - plc_y[0];
estop_x = 32;
rail_z  = Hz - plc_depth - rail_gap - rail_h;  // underside of the rail
rail_x0 = ox - rail_len / 2;
function slot_x(i) = i == 0 ? rack_x0 : slot_x(i - 1) + wagos[i - 1] + 2 * arm_t + slot_gap;   // left edge of slot i, cavity x
corners = [for (i = [0, 1], j = [0, 1]) [boss_r + (cx - 2 * boss_r) * i, boss_r + (cy - 2 * boss_r) * j]];

assert(x_left + win.x + usb_notch[0] < cx - 4, "USB notch reaches the right wall: reduce usb_notch or increase right_room");
assert(estop_x + 20 < rail_x0, "E-STOP body overlaps the rail: move the window right (x_left) or shorten the rail");
assert(slot_x(len(wagos) - 1) + wagos[len(wagos) - 1] + 2 * arm_t < cx - 4, "Wago rack reaches the right wall: move rack_x0 left");
assert(rail_z > floor_t + 8, "unit sits too low: the box is too short for the rail pedestals");

module footprint() { offset(r_out) offset(-r_out) square([W, D]); }
module cav() { translate([t, t, 0]) children(); }
module oval(w, h, len) {   // hull of two circles along x, extruded along z
    hull() for (s = [-1, 1]) translate([s * (w - h) / 2, 0, 0]) cylinder(d = h, h = len);
}

// ---------- base ----------
module columns() {
    for (c = corners) hull() {
        translate([c.x, c.y, floor_t - 0.01]) cylinder(r = boss_r, h = H - floor_t + 0.01);
        translate([c.x < cx / 2 ? 0 : cx - 1, c.y < cy / 2 ? 0 : cy - 1, floor_t - 0.01]) cube([1, 1, H - floor_t + 0.01]);
    }
}

module pedestals() {
    for (s = rail_slots) translate([rail_x0 + s - 6, oy - 15, floor_t - 0.01]) cube([12, 30, rail_z - floor_t + 0.01]);
}

module wago_rack() {   // wall at cavity y = 0, material grows to +y
    for (i = [0 : len(wagos) - 1]) {
        ds = wago_h[i];
        d0 = ds - wago_grip;     // the lip starts here, overhang 0, growing at 45 degrees
        da = d0 + lip + 1.2;     // arm depth: slope, then the 1.2 mm lead-in ramp
        x0 = slot_x(i);
        w = wagos[i];
        // ledge under the connector, 45 degrees underneath so it prints without support
        hull() {
            translate([x0, -0.01, rack_z - ds]) cube([2 * arm_t + w, 0.02, ds]);
            translate([x0, 0, rack_z - 0.01]) cube([2 * arm_t + w, ds, 0.01]);
        }
        for (side = [0, 1]) translate([x0 + side * (arm_t + w), 0, 0]) {
            translate([0, 0, rack_z]) cube([arm_t, da, arm_h]);
            translate([side == 0 ? arm_t : 0, 0, rack_z + arm_h / 2]) mirror([side, 0, 0])
                linear_extrude(arm_h / 2) polygon([[0, d0], [lip, d0 + lip], [0, da]]);
        }
    }
}

module cs_hole() {
    translate([0, 0, -1]) cylinder(d = wood_d, h = floor_t + 2);
    translate([0, 0, floor_t - (wood_head - wood_d) / 2]) cylinder(d1 = wood_d, d2 = wood_head, h = (wood_head - wood_d) / 2 + 0.01);
}

module base() {
    difference() {
        union() {
            difference() {
                linear_extrude(H) footprint();
                translate([t, t, floor_t]) cube([cx, cy, H]);
            }
            cav() { columns(); pedestals(); wago_rack(); }
        }
        cav() {
            for (c = corners) translate([c.x, c.y, H - insert_h - 0.5]) cylinder(d = insert_d, h = insert_h + 1);
            for (s = rail_slots) translate([rail_x0 + s, oy, rail_z - insert_h - 0.5]) cylinder(d = insert_d, h = insert_h + 1);
        }
        // cable opening and tie slots, back wall
        translate([t + ox, D - t - 1, exit_z]) rotate([-90, 0, 0]) oval(exit_d.x, exit_d.y, t + 2);
        for (s = [-1, 1]) translate([t + ox + s * (exit_d.x / 2 + 8), D - t - 1, exit_z - 2]) rotate([-90, 0, 0])
            translate([-2.1, -0.9, 0]) cube([4.2, 1.8, t + 2]);
        // DC jack, back wall, right
        translate([t + cx - 15, D - t - 1, jack_z]) rotate([-90, 0, 0]) cylinder(d = jack_d, h = t + 2);
        // POWER rocker, left wall, thinned from inside
        translate([-1, t + rocker_y, rocker_z]) rotate([0, 90, 0]) cylinder(d = rocker_d, h = t + 2);
        translate([rocker_panel, t + rocker_y, rocker_z]) rotate([0, 90, 0]) cylinder(d = rocker_recess, h = t);
        if (wood_screw_holes) for (p = [[13, 12], [cx - 13, 12], [13, cy - 12], [cx - 13, cy - 12]])
            translate([t + p.x, t + p.y, 0]) cs_hole();
    }
}

// ---------- lid ----------
module lip() {   // locating lip inside the cavity, open at the corner columns
    lip_h = 3; lip_w = 1.2; c = 0.3;
    translate([0, 0, H - lip_h]) cav() difference() {
        translate([c, c, 0]) difference() {
            cube([cx - 2 * c, cy - 2 * c, lip_h]);
            translate([lip_w, lip_w, -1]) cube([cx - 2 * (c + lip_w), cy - 2 * (c + lip_w), lip_h + 2]);
        }
        for (p = corners) translate([p.x < cx / 2 ? -1 : cx - 2 * boss_r - 3, p.y < cy / 2 ? -1 : cy - 2 * boss_r - 3, -1])
            cube([2 * boss_r + 4, 2 * boss_r + 4, lip_h + 2]);
    }
}

module lid() {
    difference() {
        union() { translate([0, 0, H]) linear_extrude(lid_t) footprint(); lip(); }
        cav() {
            translate([x_left, fm, H - 1]) cube([win.x, win.y, lid_t + 2]);
            translate([estop_x, cy / 2, H - 1]) cylinder(d = hole_d, h = lid_t + 2);
            translate([x_left + win.x - 0.01, oy + usb_y - usb_notch[1] / 2, H - 1]) cube([usb_notch[0], usb_notch[1], lid_t + 2]);
            for (c = corners) translate([c.x, c.y, H - 1]) cylinder(d = screw_d, h = lid_t + 2);
        }
    }
}

module usb_plug() {   // fills the notch, held by a flange on the lid; pull it out with a fingernail
    play = 0.2; fl = 2; fl_t = 1.2;
    w = usb_notch[1] - 2 * play;
    cube([usb_notch[0] - play, w, lid_t - 0.2]);
    translate([0, -fl, lid_t - 0.21]) cube([usb_notch[0] - play + fl, w + 2 * fl, fl_t]);
}

module estop_ring() difference() {
    cylinder(d = estop_ring[0], h = estop_ring[1], $fn = 96);
    translate([0, 0, -1]) cylinder(d = hole_d, h = estop_ring[1] + 2);
}

// ---------- preview ----------
module ghosts() {
    color("silver") translate([t + rail_x0, t + oy - rail_w / 2, rail_z]) cube([rail_len, rail_w, rail_h]);
    cav() translate([ox, oy, Hz]) {   // StamPLC
        color("#222") translate([-plc_w / 2, plc_y[0], -10]) cube([plc_w, plc_y[1] - plc_y[0], 10]);
        color("#333") translate([-plc_w / 2, -36, -plc_depth]) cube([plc_w, 72, plc_depth - 10]);
    }
    color("red") translate([t + estop_x, t + cy / 2, Hz - estop_depth]) cylinder(d = 30, h = estop_depth + 20);
    color("#3b82f6") translate([0, t + rocker_y, rocker_z]) rotate([0, 90, 0]) cylinder(d = rocker_d, h = 22);
    for (i = [0 : len(wagos) - 1]) color("orange", 0.8) cav() translate([slot_x(i) + arm_t, 0, rack_z]) cube([wagos[i], wago_h[i], 18.6]);
    color("#333") translate([t + cx - 15, D - 22, jack_z]) rotate([-90, 0, 0]) cylinder(d = 12, h = 22);
}

module body_colored() { color("#3a6ea5") render() base(); }
module lid_colored(dz = 0) { translate([0, 0, dz]) { color("#2b2f36") render() lid(); color("gold") translate([t + estop_x, t + cy / 2, Hz]) estop_ring(); } }

if      (part == "base")       base();
else if (part == "lid")        translate([0, D, Hz]) rotate([180, 0, 0]) lid();   // face down on the bed
else if (part == "estop_ring") estop_ring();                                       // print in yellow, flat
else if (part == "usb_plug")   usb_plug();
else if (part == "exploded")   { body_colored(); lid_colored(30); }
else                           { body_colored(); lid_colored(); %ghosts(); }
