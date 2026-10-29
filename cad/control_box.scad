// Control box — all electrics in one box, 24 V DC only (rev. 2026-10-07, "safe edition").
//   Front:  45° console plate, a separate part like the lid (rev. 2026-10-07): E-STOP (S3, on a yellow ring),
//           STOP (S2), START (S0), JOG (S1) and POWER (Q1, round Ø20 mm snap-in rocker with 24 V LED).
//           Fit and wire the buttons on the bench, then screw the plate into its frame. It rests on a ledge
//           all round and on two pillars, one right of the E-STOP, so a hard hit goes into the base, not the screws.
//   Middle: DIN rail with K1–K4 (PYF08A + HH52P-L) and the timer T1 (DH48S-S), front through the lid.
//   Back:   DC jack J1 (low) and fuse holder F1 (T 1 A, higher, offset to the right) at the left end, each with
//           room for an open-end spanner (head Ø40 clear, handle up), and by default the 5 × M12 field
//           cable glands (option glands_on = "left" puts them in the left wall instead).
// No mains inside: a closed, CE-marked desktop supply (Mean Well GST25A24-P1J, own IEC inlet)
// stays on the bench and plugs into J1.
// Cables: all low. Glands at 22 mm; at the back they lead into the floor channel behind the sockets
// (y 170–198, 28 mm: room for a ferruled wire to turn in front of the gland nuts), at the left into the
// zone left of the rail. Mount the sockets with their 1/4 (NC/NO) end towards the back wall: only 4 wires
// land on its low screw row, against 14 plus the diode legs on the 13/14 end.
// No right-wall option: the timer and the rail end stop leave 4–13 mm there.
// The box breathes through the LED windows and the timer cut-out (about 5 W of coils, no PSU inside).
//
// Coordinates: X along the console (E-STOP at -X, POWER at +X), Y = 0 is the
// operator face, Z up. Origin = outer front-left-bottom corner.
//
// Printers: base 245 × 201, lid 245 × 138, plate 240 × 82: fits the Bambu P2S (256) and the QIDI Max4.
// Print: PETG or ASA, 4 perimeters, 15–20 % infill, no supports.
//        Base upright (the console frame and ledges are 45° overhangs), lid and plate face down.
// Labels: engraved; each label part fills its part's engravings in a second colour and
//        is exported with its part (same frame, so drag both into the slicer as one object):
//        "labels_base" with the base (back or left wall), "labels_plate" with the plate and "labels_lid" with
//        the lid (both lie flat on the bed with their part). The relay LED windows stay open.
//        Single colour: leave the labels out (engravings stay empty or get painted).
// E-STOP ring (part = "estop_ring"): print in yellow, fit it under the E-STOP bezel.
// Hardware: 4 × M3×8 + 4 × M3 heat-set inserts (lid), 6 × M3×8 countersunk + 6 × inserts (plate),
//           3 × M3×6 pan-head + washers + 3 × M3 heat-set inserts (rail), 5 × M12 cable glands,
//           DIN rail 35 mm cut to 211 mm + 2 end stops, and with wood_screw_holes = true
//           4 × 4 mm countersunk wood screws (box).
// Wagos: a clip rack on the back wall above the glands. Each connector stands on edge, wire entries up (you wire
//        from above with the lid off), levers towards the relays, and snaps between two flexible arms.
// Fit order: base (to the board with wood_screw_holes) → inserts, rail → J1, F1 → glands → Wagos into the rack → buttons and Q1 into the plate (bench)
// → wire → plate → lid. Q1 snaps in from the front; the plate is thinned to rocker_panel around its hole.
// Leave the button wires long enough to lay the plate face down in front of the box.

wood_screw_holes = false;   // true: 4 countersunk holes in the base floor for 4 mm wood screws (box on a wooden board)
part = "assembly";     // "base" | "plate" | "lid" | "labels_base" | "labels_plate" | "labels_lid" | "estop_ring" | "rack_test" | "assembly" | "exploded"
glands_on = "back";    // field cable glands: "back" (default, valve and QPM11 sit behind the box) | "left"
$fn = 48;

// ---- bought parts: measure yours and adjust ----
sock        = [23, 72];       // PYF08A footprint: along rail × across (+ 4 mm DIN latch at the 13/14 end)
relay_top   = 72;             // relay top above the floor with the rail flat on it (the preview adds rail_lift)
timer_w     = 48;             // DH48S front, square
timer_top   = 112;            // timer front above the floor with the rail flat on it (preview only, adds rail_lift)
rail_w      = 35;
gland_d     = 12.5;           // M12 thread
hole_d      = 22.4;           // 22 mm operators, panel 1–6 mm
estop_ring  = [56, 1.5];      // yellow ring under the E-STOP bezel, Ø × thick: plate 3 + 1.5 stays within 6 mm
rocker_d    = 20.2;           // Q1 round snap-in rocker, Ø20 mm
rocker_panel = 2;             // its clips want a thin panel: plate thinned to this from inside
rocker_recess = 28;           // Ø of that thinning
// back wall entries, x in the cavity. Behind the sockets 28 mm are free (they end at y 170): room for
// the gland nuts, the wires that turn in front of them and the power entry bodies (F1 25 mm, J1 22 mm).
entry_z = 22;   // glands: low, cables run along the floor
spanner = 20;   // clear radius around each nut in the wall plane: open-end head of a 17 mm spanner (Wera Joker ≈ Ø40)
// field cables: position along the wall (back: cavity x, pitch 30, spread over the wall right of J1's spanner room;
// left: y, pitch 20, clear of the front lid column), label
gland_u = glands_on == "left" ? [86, 106, 126, 146, 166] : [80, 110, 140, 170, 200];
glands  = [for (i = [0 : 4]) [gland_u[i], ["Y1", "Y2", "P", "B0", "B1"][i]]];
module at_gland(u) {   // local frame on the outer wall face, +z pointing into the box
    if (glands_on == "left") translate([0, u, entry_z]) rotate([0, 90, 0]) children();
    else translate([c0 + u, D, entry_z]) rotate([90, 0, 0]) children();
}
// power: [x, z, hole Ø, depth behind the panel (preview), label, label z]
// J1 panel DC jack 5.5 × 2.1 mm, 8 mm thread (DC-099 type, user's part 2026-10-09; centre +, matches the GST …-P1J
// plug). F1 panel fuse holder 5 × 20 mm, IP65,
// pre-wired (user's listing, 2026-10-06): 12 mm hole, 28 mm from the flange to the body end incl. the wall, cap 13 mm
// outside, two 145 mm 0.75 mm² leads. Inside the body ends at y 172.6, 2.6 mm behind the socket row (y 170).
// Spanner room (user, 2026-10-07): J1 low, `spanner` clear of the corner column (x < 9) and the first gland; F1 above
// the gland row and offset right, so the spanner on J1 swings up past F1, and F1's head stays clear of the Wago rack.
power = [[9 + spanner + 1, 22, 8.2, 22, "24V DC", 8], [50, 60, 12.5, 25.4, "T1A", 74]];   // 28 − wall 2.6

// Wago 221 rack, left to right as on the wiring board: X-EN, X-M1, X-M2 (221-415), X-D (221-413), the D6 and D7
// joints (221-412). Widths measured with calipers (user, 2026-10-05: the data-sheet sizes + 0.2 play were very loose in
// the test print; they match 5.6 · poles + 1.75). Heights:
// WAGO data sheets 8.4 (221-415), 8.3 (221-412/413); real parts run 0.1–0.3 under nominal, so the lip grips instead
// of fitting: its retaining face is a 45° slope that starts wago_grip below nominal, and the arm spring presses it onto
// the rim of the lever face, pulling the connector against the wall for any height from nominal − grip to + lip − grip.
wagos     = [29.7, 29.7, 29.7, 18.5, 13.0, 13.0];
wago_h    = [8.4, 8.4, 8.4, 8.3, 8.3, 8.3];   // nominal housing height = ledge depth from the wall
wago_d    = 18.6;     // housing depth, standing vertically (preview only)
wago_fit  = 0;        // no added play in width: printed slots come out a little narrow, the arms flex
arm_t     = 1.4;      // snap arm: thickness, height, lip over the rim of the lever face
arm_h     = 16;
lip       = 0.8;
wago_grip = 0.5;      // arm preload at nominal height (lip slope 45°: covers heights nominal − 0.5 … + 0.3)
slot_gap  = 1;        // between the arms of neighbouring slots, so each arm can flex
rack_x0   = power[1][0] + spanner + 2;   // cavity x of the first slot: clear of the spanner on F1 (72)
rack_z    = 42;       // underside of the connectors: the 45° ledges below stay above the gland nuts (z < 31)

// ---- box ----
t       = 2.6;                // wall
floor_t = 3;
lid_t   = 3;
r_out   = 3;
Hz      = 83;                 // rim height: interior 80 above the floor
zs      = 20;                 // front skirt height
a       = 45;                 // console slope from horizontal (45° prints without support)
cx      = 240;                // cavity width: power entry with spanner room + Wago rack + corner columns
in_back = 198;                // inner face of the back wall (y)
W  = t + cx + t;              // 221.2
D  = in_back + t;             // 200.6
ys = (Hz - zs) / tan(a);      // where the console meets the top (lid front edge)
L  = (Hz - zs) / sin(a);      // console slope length (89.1)
c0 = t;                       // cavity x range
c1 = t + cx;

// console: buttons on the slope, s = distance up the slope from the skirt edge, w outward from the face
s_row   = 55;
s_label = 15;
// x in the cavity, label, bezel Ø, depth behind the panel (preview only), hole Ø. E-STOP far left, POWER far right.
buttons = [
    [40,  "E-STOP",  40, 55, hole_d],
    [96,  "STOP",    30, 45, hole_d],    // 13 mm clear of the E-STOP ring
    [136, "START",   30, 45, hole_d],
    [176, "JOG",     30, 45, hole_d],
    [216, "POWER",   24, 30, rocker_d],
];
// console plate (user, 2026-10-07: separate like the lid, but solid). It sits flush in a pocket of the 45° frame:
// side walls, a band at the skirt (fb) and one under the lid (ft). Behind its edges a ledge (lw wide, ledge_t thick)
// carries it; two pillars from the floor carry it between the buttons, one right of the E-STOP, one left of POWER.
// Contact blocks (30 wide, preview) pass through the opening, so a wired plate goes in and out in one piece.
plate_t = 3;
ledge_t = 2.5;
ct      = plate_t + ledge_t;  // frame depth behind the console face
lw      = 7;
fb      = 3;
ft      = 4;
pgap    = 0.3;                // play around the plate
y_in_top = ys + ct / sin(a);  // inner frame face at rim height
pillars = [68, 198];          // cavity x: E-STOP body ≤ 60 | STOP block ≥ 81; JOG block ≤ 191 | Q1 body ≥ 205
pillar_w = 6;
s_screw = [fb + 4.5, L - ft - 4.5];   // M3 countersunk, heads clear of the plate edge
plate_screws = concat([for (x = [4.5, cx - 4.5], s = s_screw) [x, s]], [for (x = pillars) [x, s_screw[1]]]);

// DIN rail, cavity x: cut to 211 mm, 12.5 mm from a slot centre at the K1 end, 13.5 mm left of the K1 end stop,
// so the insert pads land on slot centres (12.5 + 25·k from the rail end: k = 1, 5, 7).
rail_len = 211;
rail_y  = 134;                // sockets span 98–170: room for the button bodies in front
stop_w  = 8;
pitch   = 30;
timer_hole = 50;              // timer front passes through, so the lid lifts off over it
led_slot = [8, 36];
// Device row (user, 2026-10-06): centred under the lid. The visible group runs from the K1 LED window to the right
// edge of the timer cut-out; row_x0 = left end of the K1 end stop. F1 and J1 sit behind the socket row (y > 170).
row_x0  = cx / 2 - (stop_w + pitch / 2 - led_slot.x / 2 + stop_w + 4 * pitch + 25 + timer_hole / 2) / 2;   // 21.5
relay_x = [for (i = [0 : 3]) row_x0 + stop_w + pitch / 2 + i * pitch];
timer_x = row_x0 + stop_w + 4 * pitch + 25;
rail_x0 = row_x0 - 13.5;      // rail start (8)
rail_holes = [for (k = [1, 5, 7]) 12.5 + 25 * k];   // 37.5, 137.5, 187.5 from rail_x0: under K1, K4 edge, right of T1's socket


boss_r   = 4.5;
insert_d = 4.2;               // M3 heat-set insert; 2.6 for self-tapping M3
insert_h = 6;
// Rail pads: the floor (3) is too thin for an insert, so the rail stands on three pads. Hole insert_h + 0.5 deep,
// 1 mm of plastic left under it; the rail lifts by rail_lift, the ribs and the ghosts follow.
insert_play = 0.5;
rail_lift = insert_h + insert_play + 1 - floor_t;   // 4.5
screw_d  = 3.4;

wood_d    = 4.5;
wood_head = 9;
// [x, y] world; all reachable from above with the lid off
// back ones in front of the corner columns and the Wago rack, so a screwdriver goes straight down
wood_holes = [[c0 + 13, 86], [c1 - 13, 86], [c0 + 15, in_back - 14], [c1 - 14, in_back - 16]];

label_depth = 0.8;            // 4 layers at 0.2 mm: light colours stay opaque
font = "Liberation Sans:style=Bold";

// ---------- profile ----------
// YZ outline, extruded along X; the tall one also shapes the lid front edge
P      = [[0, 0], [D, 0], [D, Hz], [ys, Hz], [0, zs]];
P_tall = [[0, 0], [D, 0], [D, Hz + 20], [ys + 20 / tan(a), Hz + 20], [0, zs]];

module xprof(x0, x1) { translate([x0, 0, 0]) rotate([90, 0, 90]) linear_extrude(x1 - x0) children(); }
module footprint() { offset(r_out) offset(-r_out) square([W, D]); }
module cavity_2d() {
    intersection() {
        offset(delta = -t) polygon(P_tall);
        translate([0, floor_t]) square([D, Hz + 1 - floor_t]);
    }
}
module sframe() { translate([0, 0, zs]) rotate([a, 0, 0]) children(); }   // console face, w outward

// ---------- base ----------
bosses = [[c0 + boss_r, y_in_top + boss_r], [c1 - boss_r, y_in_top + boss_r],
          [c0 + boss_r, in_back - boss_r],  [c1 - boss_r, in_back - boss_r]];

module boss(c) {   // hull to the side wall, and to the back wall at the back
    wx = c.x < W / 2 ? c0 : c.x;
    difference() {
        hull() {
            translate([c.x, c.y, 0]) cylinder(r = boss_r, h = Hz);
            translate([wx, c.y - boss_r, 0]) cube([boss_r, 2 * boss_r, Hz]);
            if (c.y > D / 2) translate([c.x - boss_r, c.y, 0]) cube([2 * boss_r, boss_r, Hz]);
        }
        translate([c.x, c.y, Hz - insert_h]) cylinder(d = insert_d, h = insert_h + 1);
    }
}

module rail_ribs() {
    for (s = [-1, 1]) translate([c0 + rail_x0, rail_y + s * (rail_w / 2 + 0.3) + (s < 0 ? -2 : 0), floor_t])
        cube([rail_len, 2, rail_lift + 1.5]);
    for (x = rail_holes) translate([c0 + rail_x0 + x, rail_y, floor_t - 0.01]) cylinder(r = boss_r, h = rail_lift + 0.01);
}

module cs_hole() {
    translate([0, 0, -1]) cylinder(d = wood_d, h = floor_t + 2);
    translate([0, 0, floor_t - (wood_head - wood_d) / 2]) cylinder(d1 = wood_d, d2 = wood_head, h = (wood_head - wood_d) / 2 + 0.01);
}

module base_labels(extra = 0) {   // world coords; extra > 0 for the cut
    if (glands_on == "left") for (g = glands)   // left wall, read from the left
        translate([label_depth, g[0], entry_z + 13]) multmatrix([[0, 0, -1, 0], [-1, 0, 0, 0], [0, 1, 0, 0]])
            linear_extrude(label_depth + extra) text(g[1], size = 5, font = font, halign = "center", valign = "center");
    // back wall, read from behind: above each entry
    for (l = concat(glands_on == "left" ? [] : [for (g = glands) [g[0], g[1], 5, entry_z + 13]],
                    [for (p = power) [p[0], p[4], 4, p[5]]]))
        translate([c0 + l[0], D - label_depth, l[3]]) multmatrix([[-1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0]])
            linear_extrude(label_depth + extra) text(l[1], size = l[2], font = font, halign = "center", valign = "center");
}

// left edge of slot i, cavity x
function slot_x(i) = i == 0 ? rack_x0 : slot_x(i - 1) + wagos[i - 1] + wago_fit + 2 * arm_t + slot_gap;
module wago_rack() {
    for (i = [0 : len(wagos) - 1]) {
        ds = wago_h[i];                           // ledge depth from the wall
        d0 = wago_h[i] - wago_grip;               // the lip starts here, overhang 0, growing at 45°
        da = d0 + lip + 1.2;                      // arm depth: slope, then the 1.2 mm lead-in ramp
        x0 = c0 + slot_x(i);
        w = wagos[i] + wago_fit;
        xo = 2 * arm_t + w;
        // ledge under the connector, 45° underneath so it prints without support
        hull() {
            translate([x0, in_back - 0.01, rack_z - ds]) cube([xo, 0.01, ds]);
            translate([x0, in_back - ds, rack_z - 0.01]) cube([xo, ds, 0.01]);
        }
        // two arms standing on the ledge; the lip: lead-in ramp at the front, 45° gripping slope towards the wall
        for (side = [0, 1]) translate([x0 + side * (arm_t + w), 0, 0]) {
            translate([0, in_back - da, rack_z]) cube([arm_t, da, arm_h]);
            translate([side == 0 ? arm_t : 0, in_back, rack_z + arm_h / 2]) mirror([side, 0, 0])
                linear_extrude(arm_h / 2) polygon([[0, -d0], [lip, -d0 - lip], [0, -da]]);
        }
    }
}

// ---------- console frame and plate (sframe coords: x world, s up the slope, w outward) ----------
module outer_body() { intersection() { linear_extrude(Hz) footprint(); xprof(-1, W + 1) polygon(P); } }

module frame_slab() {   // thickens the console to ct behind the face, clipped to the box outline
    intersection() { outer_body(); sframe() translate([c0 - 1, -10, -ct]) cube([cx + 2, L + 20, ct]); }
}

module frame_cuts() {
    translate([c0, fb, -plate_t]) cube([cx, L - ft - fb, plate_t + 5]);                               // pocket
    translate([c0 + lw, fb + lw, -ct - 1]) cube([cx - 2 * lw, L - ft - fb - 2 * lw, ct + 6]);           // opening
}

module plate_boss(x, s) {   // insert boss behind the ledge, along -w
    translate([c0 + x, s, -plate_t - insert_h - 2]) cylinder(r = boss_r, h = insert_h + 2);
}

module plate_supports() {   // insert bosses (corners hulled to the side wall) and the pillars
    intersection() {
        outer_body();
        sframe() for (p = plate_screws) hull() {
            plate_boss(p.x, p.y);
            if (p.x < 10 || p.x > cx - 10)
                translate([p.x < cx / 2 ? c0 - 1 : c1 - 0.01, p.y - boss_r, -plate_t - insert_h - 2]) cube([1.01, 2 * boss_r, insert_h + 2]);
        }
    }
    for (x = pillars) hull() {
        sframe() translate([c0 + x - pillar_w / 2, 40, -ct]) cube([pillar_w, L - ft - 40, ct - plate_t]);   // pad under the plate
        translate([c0 + x - pillar_w / 2, 40, floor_t - 0.01]) cube([pillar_w, 18, 0.01]);                // foot
    }
}

module base() {
    difference() {
        union() {
            difference() {
                union() { difference() { outer_body(); xprof(c0, c1) cavity_2d(); } frame_slab(); }
                sframe() frame_cuts();
            }
            for (b = bosses) boss(b);
            rail_ribs();
            wago_rack();
            plate_supports();
        }
        sframe() for (p = plate_screws) translate([c0 + p.x, p.y, -plate_t - insert_h - 0.5]) cylinder(d = insert_d, h = insert_h + 0.51);
        for (g = glands) at_gland(g[0]) translate([0, 0, -1]) cylinder(d = gland_d, h = t + 2);
        for (p = power) translate([c0 + p[0], in_back - 1, p[1]]) rotate([-90, 0, 0]) cylinder(d = p[2], h = t + 2);
        for (x = rail_holes) translate([c0 + rail_x0 + x, rail_y, floor_t + rail_lift - insert_h - insert_play])
            cylinder(d = insert_d, h = insert_h + insert_play + 1);
        if (wood_screw_holes) for (h = wood_holes) translate([h.x, h.y, 0]) cs_hole();
        base_labels(1);
    }
}

// ---------- lid ----------
module lid_shape() {   // front edge continues the console slope
    intersection() {
        translate([0, 0, Hz]) linear_extrude(lid_t) footprint();
        translate([0, ys - 1, Hz]) cube([W, D, lid_t]);
        xprof(-1, W + 1) polygon(P_tall);
    }
}

module lip() {   // locating lip inside the cavity
    lip_h = 3; lip_w = 1.2; c = 0.3;
    translate([0, 0, Hz - lip_h]) difference() {
        translate([c0 + c, y_in_top + c, 0]) cube([cx - 2 * c, in_back - y_in_top - 2 * c, lip_h]);
        translate([c0 + c + lip_w, y_in_top + c + lip_w, -1])
            cube([cx - 2 * (c + lip_w), in_back - y_in_top - 2 * (c + lip_w), lip_h + 2]);
        for (b = bosses) {
            translate([b.x, b.y, -1]) cylinder(r = boss_r + 1, h = lip_h + 2);
            translate([b.x < W / 2 ? c0 : b.x, b.y - boss_r - 1, -1]) cube([boss_r + 1, 2 * boss_r + 2, lip_h + 2]);
            if (b.y > D / 2) translate([b.x - boss_r - 1, b.y, -1]) cube([2 * boss_r + 2, boss_r + 1, lip_h + 2]);
        }
    }
}

module led_window() { linear_extrude(lid_t + 2) offset(led_slot.x / 2) square([0.01, led_slot.y - led_slot.x], center = true); }

module lid_marks(extra = 0) {   // world coords
    translate([0, 0, Hz + lid_t - label_depth]) linear_extrude(label_depth + extra) {
        for (i = [0 : len(relay_x) - 1]) translate([c0 + relay_x[i], rail_y - led_slot.y / 2 - 7])
            text(str("K", i + 1), size = 6, font = font, halign = "center", valign = "center");
        translate([c0 + timer_x, rail_y - timer_hole / 2 - 7]) text("T1", size = 6, font = font, halign = "center", valign = "center");
    }
}

module lid() {
    difference() {
        union() { lid_shape(); lip(); }
        for (b = bosses) translate([b.x, b.y, Hz - 1]) cylinder(d = screw_d, h = lid_t + 2);
        translate([c0 + timer_x - timer_hole / 2, rail_y - timer_hole / 2, Hz - 1]) cube([timer_hole, timer_hole, lid_t + 2]);
        for (x = relay_x) translate([c0 + x, rail_y, Hz - 1]) led_window();
        lid_marks(1);
    }
}

module labels_lid() { lid_marks(); }   // labels only: the LED windows stay open

// ---------- plate (sframe coords) ----------
module plate_labels(extra = 0) {
    for (b = buttons) translate([c0 + b[0], s_label, -label_depth])
        linear_extrude(label_depth + extra) text(b[1], size = 5, font = font, halign = "center", valign = "center");
}

module plate() {
    difference() {
        translate([c0 + pgap, fb + pgap, -plate_t]) cube([cx - 2 * pgap, L - ft - fb - 2 * pgap, plate_t]);
        for (b = buttons) translate([c0 + b[0], s_row, -plate_t - 1]) {
            cylinder(d = b[4], h = plate_t + 2);
            if (b[4] == rocker_d) cylinder(d = rocker_recess, h = 1 + plate_t - rocker_panel);
        }
        for (p = plate_screws) translate([c0 + p.x, p.y, 0]) {   // M3 countersunk, 90°
            translate([0, 0, -plate_t - 1]) cylinder(d = screw_d, h = plate_t + 2);
            translate([0, 0, -3.2 + 0.01]) cylinder(d1 = 0, d2 = 6.4, h = 3.2);
        }
        plate_labels(1);
    }
}

module plate_flat() { translate([0, L, 0]) rotate([180, 0, 0]) children(); }   // face down on the bed

// ---------- preview ----------
module ghosts() {   // bought parts
    for (i = [0 : len(wagos) - 1]) color("orange", 0.8)
        translate([c0 + slot_x(i) + arm_t + wago_fit / 2, in_back - wago_h[i], rack_z]) cube([wagos[i], wago_h[i], wago_d]);
    color("silver") translate([c0 + rail_x0, rail_y - rail_w / 2, floor_t + rail_lift]) cube([rail_len, rail_w, 7.5]);
    for (x = relay_x) translate([c0 + x, rail_y, floor_t + rail_lift]) {
        color("#222") translate([-sock.x / 2, -sock.y / 2, 4.1]) cube([sock.x, sock.y, 31]);
        color("white", 0.8) translate([-11, -14, 32.5]) cube([22, 28, relay_top - 32.5]);
    }
    color("beige") translate([c0 + timer_x, rail_y, floor_t + rail_lift + 35]) {   // 44.5 body under a 48 bezel, 10 deep
        translate([-22.25, -22.25, 0]) cube([44.5, 44.5, timer_top - 35 - 10]);
        translate([-timer_w / 2, -timer_w / 2, timer_top - 35 - 10]) cube([timer_w, timer_w, 10]);
    }
    for (p = power) {
        color("#333") translate([c0 + p[0], in_back - p[3], p[1]]) rotate([-90, 0, 0]) cylinder(d = p[2] - 1, h = p[3]);
        color("silver") translate([c0 + p[0], D, p[1]]) rotate([-90, 0, 0]) cylinder(d = p[2] + 4, h = 3, $fn = 6);
    }
    sframe() for (b = buttons) translate([c0 + b[0], s_row, 0]) {
        color(b[1] == "E-STOP" ? "red" : b[1] == "START" ? "green" : b[1] == "JOG" ? "white" : b[1] == "POWER" ? "#3b82f6" : "#333")
            translate([0, 0, b[1] == "E-STOP" ? estop_ring[1] : 0]) cylinder(d = b[2], h = b[1] == "E-STOP" ? 22 : 10);
        color("white") translate([-15, -15, -b[3]]) cube([30, 30, b[3] - t]);
    }
    for (g = glands) color("#444") at_gland(g[0]) translate([0, 0, -9]) cylinder(d = 16, h = 9, $fn = 6);
}

module estop_ring() difference() {
    cylinder(d = estop_ring[0], h = estop_ring[1], $fn = 96);
    translate([0, 0, -1]) cylinder(d = hole_d, h = estop_ring[1] + 2);
}

module body_colored() { color("#3a6ea5") render() base(); color("white") render() base_labels(); }
module plate_colored(dw) {
    sframe() translate([0, 0, dw]) {
        color("#2b2f36") render() plate(); color("white") render() plate_labels();
        color("gold") translate([c0 + buttons[0][0], s_row, 0]) estop_ring();
    }
}
module lid_colored(dz) { translate([0, 0, dz]) { color("#2b2f36") render() lid(); color("white") render() labels_lid(); } }

if      (part == "base")        base();
else if (part == "labels_base") base_labels();
// lid and its labels: flipped face down onto the bed, same transform for both
else if (part == "lid")         translate([0, D, Hz + lid_t]) rotate([180, 0, 0]) lid();
else if (part == "plate")        plate_flat() plate();
else if (part == "labels_plate") plate_flat() plate_labels();
// test print for the Wago snap fit: floor and back wall cut out of the base around the 221-415 slot (X-EN) and
// the 221-413 + two 221-412 slots, printed upright like the base
else if (part == "rack_test") {
    s3 = c0 + slot_x(3) - slot_gap / 2;   // cut in the gaps between slots, never on an arm face
    for (r = [[c0 + slot_x(0) - 1, c0 + slot_x(1) - slot_gap / 2, 0], [s3, c0 + slot_x(5) + wagos[5] + wago_fit + 2 * arm_t + 1, slot_x(1) - slot_x(3) + 4]])
        translate([r[2], 0, 0]) intersection() { base(); translate([r[0], in_back - 14, -1]) cube([r[1] - r[0], 30, rack_z + wago_d + 3]); }
}
else if (part == "estop_ring")  estop_ring();   // print in yellow, flat
else if (part == "labels_lid")  translate([0, D, Hz + lid_t]) rotate([180, 0, 0]) labels_lid();
else if (part == "exploded")    { body_colored(); plate_colored(60); lid_colored(70); }
else if (part == "assembly")    { body_colored(); plate_colored(0); lid_colored(0); %ghosts(); }
else                            assert(false, str("unknown part: ", part));
