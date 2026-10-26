// Crank Clamp for Lee APP Press Lever (pneumatic conversion)
// ----------------------------------------------------------------
// Two printed halves clamp over the edges of the two flat lever struts (V shape)
// and are bolted together through the V gap. A side arm with a pivot hole takes
// the air cylinder rod end. Assembled, both arms form one solid plate in the
// middle of the lever height. A wedge gusset blends the clamp into the arm.
//
// Print: "print_plate" puts both halves on the bed, parting plane down, no supports.
// Hardware: 2x clamp bolt + nut + washers, 1x pivot bolt + nut + washers.
//
// Coordinates (assembled):
//   X = along the lever (x=0: narrow end of the V, x=L: wide end)
//   Y = across, straight strut inner face at y=0
//   Z = strut width = bolt direction

/* [Output] */
// Which part to show / export. Use "print_plate" for printing, "assembly" to check fit.
part = "print_plate"; // [print_plate:Print plate (both halves), assembly:Assembly view, top:Top half only, bottom:Bottom half only]

/* [Lever geometry (measure your lever)] */
// Strut width in bolt direction (mm). Use the smallest measured value so it clamps.
strut_h = 19.2; // [10:0.1:40]
// Thickness of the straight strut (mm)
strut_t = 3.2; // [1:0.1:10]
// Thickness of the angled strut (mm)
strut_t2 = 3.3; // [1:0.1:10]
// Inner gap between the struts at the narrow end of the clamp (mm)
gap_narrow = 10; // [5:0.5:60]
// Inner gap between the struts at the wide end of the clamp (mm)
gap_wide = 30; // [10:0.5:100]
// Angle between the struts (deg). Angle gauge reading 150 = 30 here.
angle = 30; // [5:0.5:60]

/* [Clamp body] */
// Wall next to the struts, measured perpendicular to each strut (mm)
wall = 8; // [3:0.5:20]
// Plate thickness above and below the strut edges (mm)
cover = 8; // [3:0.5:20]
// Corner radius of the clamp outline (mm)
radius = 2; // [0:0.5:5]
// Chamfer on the outer edges of each half, continues along gusset and arm (mm)
chamfer = 1.5; // [0:0.25:4]
// Clearance in the strut slots (mm). Increase if it does not fit, decrease if loose.
play = 0.4; // [0:0.05:1.5]
// Air gap between the halves (mm). 0 = flush. 0.5..1 closes when tightened for extra grip.
clamp_gap = 0; // [0:0.1:2]

/* [Clamp bolts] */
// Bolt size for the 2 clamp bolts through the V gap
clamp_bolt = "M6"; // [M4, M5, M6, M8]
// Clamp bolt positions along the clamp, as fraction of its length (0 = narrow end, 1 = wide end)
clamp_bolt_pos = [0.3, 0.75];
// Override clamp hole diameter (mm). 0 = automatic from bolt size.
clamp_hole_override = 0; // [0:0.1:15]

/* [Cylinder arm] */
// Distance from the straight strut inner face to the pivot hole axis (mm). The arm is on the straight strut side.
arm_r = 30; // [15:1:100]
// Pivot position along the clamp, as fraction of its length (may be <0 or >1)
arm_x = 0.5; // [-0.5:0.05:1.5]
// Arm thickness per half at the parting plane (mm). Total plate = 2x this.
arm_t = 8; // [4:0.5:15]
// Pivot bolt size (rod end / clevis bolt)
pivot_bolt = "M10"; // [M6, M8, M10, M12]
// Override pivot hole diameter (mm). 0 = automatic from bolt size.
pivot_hole_override = 0; // [0:0.1:20]
// Extra material around the pivot hole beyond the washer (mm)
eye_extra = 3; // [1:0.5:10]

/* [Hidden] */
$fn = 64;

// Bolt table: [name, clearance hole, washer OD (ISO 7089), nut across flats]
bolts = [
    ["M4",  4.5,  9,  7],
    ["M5",  5.5, 10,  8],
    ["M6",  6.4, 12, 10],
    ["M8",  8.4, 16, 13],
    ["M10", 10.5, 20, 17],
    ["M12", 13.0, 24, 19]
];
function bolt(n) = bolts[search([n], bolts)[0]];

clamp_d  = clamp_hole_override > 0 ? clamp_hole_override : bolt(clamp_bolt)[1];
pivot_d  = pivot_hole_override > 0 ? pivot_hole_override : bolt(pivot_bolt)[1];
pivot_washer = bolt(pivot_bolt)[2];
nut_clear_r  = pivot_washer / 2 + 1;           // flat area kept free around the pivot
eye_r        = pivot_washer / 2 + eye_extra;   // eye radius around the pivot

ta      = tan(angle);
L       = (gap_wide - gap_narrow) / ta;   // clamp length
ptc     = strut_t2 / cos(angle);          // angled strut thickness measured in Y
ymin    = -strut_t - wall;
wall_s  = wall / cos(angle);              // wall next to the angled strut, measured in Y
zs      = strut_h / 2;
ztop    = strut_h + cover;
zbot    = -cover;
eye_y   = -arm_r;
y_gusset_end = eye_y + nut_clear_r;   // gusset ends where the flat washer area starts

function gap(x) = gap_narrow + x * ta;
function yb(f) = gap(f * L) / 2;

assert(chamfer < cover && chamfer < arm_t / 2, "chamfer too large for cover or arm_t");
assert(gap_wide > gap_narrow, "gap_wide must be larger than gap_narrow");
for (f = clamp_bolt_pos)
    assert(gap(f * L) >= clamp_d + 4, "V gap too narrow for the clamp bolt at this position");
assert(y_gusset_end < ymin,
       "arm_r too small for the pivot washer: increase arm_r or use a smaller pivot bolt");
echo(str("Clamp length: ", L, " mm, clamp bolts: ", clamp_bolt, " (hole ", clamp_d,
         "), pivot: ", pivot_bolt, " (hole ", pivot_d, ")"));
echo(str("Suggested bolt lengths: clamp ", clamp_bolt, "x", ceil((ztop - zbot + 9) / 5) * 5,
         ", pivot ", pivot_bolt, "x", ceil((2 * arm_t + clamp_gap + 30) / 5) * 5, " (plus rod end)"));

// ---------- 2D ----------
module outline_sharp() {
    polygon([[0, ymin], [L, ymin],
             [L, gap(L) + ptc + wall_s], [0, gap(0) + ptc + wall_s]]);
}
// Outline: corners rounded except on the arm side, which stays a flat full-width face
// so the gusset and arm blend in without steps
module arm_side_strip() { translate([0, ymin]) square([L, wall]); }
module outline() {
    union() {
        offset(r = radius) offset(delta = -radius) outline_sharp();
        arm_side_strip();
    }
}
// Arm footprint: only from the arm-side strip to the eye (never pokes out elsewhere)
module arm2d() {
    hull() {
        arm_side_strip();
        translate([arm_x * L, eye_y]) circle(r = eye_r);
    }
}
module slots() {
    translate([-1, -strut_t - play/2]) square([L + 2, strut_t + play]);
    polygon([[-1, gap(-1) - play/2], [L + 1, gap(L + 1) - play/2],
             [L + 1, gap(L + 1) + ptc + play/2], [-1, gap(-1) + ptc + play/2]]);
}
module holes() {
    for (f = clamp_bolt_pos) translate([f * L, yb(f), zbot - 1]) cylinder(d = clamp_d, h = ztop - zbot + 2);
    translate([arm_x * L, eye_y, zbot - 1]) cylinder(d = pivot_d, h = ztop - zbot + 2);
}

// ---------- Arm with gusset (local z=0 = parting plane, builds upward) ----------
// Arm footprint edges: tangent lines from the clamp corners (0,ymin) and (L,ymin) to the eye circle
function tan_pt(px, py, side) =    // side -1 = left tangent, +1 = right tangent
    let(dx = arm_x * L - px, dy = eye_y - py, d = sqrt(dx*dx + dy*dy),
        a = atan2(dy, dx) + side * asin(eye_r / d), t = sqrt(d*d - eye_r*eye_r))
    [px + t * cos(a), py + t * sin(a)];
TL = tan_pt(0, ymin, -1);
TR = tan_pt(L, ymin, +1);
function x_left(y)  = y >= TL[1] ? (y - ymin) / (TL[1] - ymin) * TL[0]
                                 : arm_x * L - sqrt(max(0, eye_r*eye_r - pow(y - eye_y, 2)));
function x_right(y) = y >= TR[1] ? L + (y - ymin) / (TR[1] - ymin) * (TR[0] - L)
                                 : arm_x * L + sqrt(max(0, eye_r*eye_r - pow(y - eye_y, 2)));

// thin slice across the arm at position y, height h, top corners chamfered
module slice(y, h) {
    xl = x_left(y); xr = x_right(y); c = min(chamfer, h / 2);
    translate([0, y + 0.01, 0]) rotate([90, 0, 0]) linear_extrude(0.01)
        polygon([[xl, 0], [xr, 0], [xr, h - c], [xr - c, h], [xl + c, h], [xl, h - c]]);
}

module arm_with_gusset(h_full) {
    difference() {
        union() {
            // arm plate, top edge chamfered
            hull() {
                linear_extrude(arm_t - chamfer) arm2d();
                translate([0, 0, arm_t - 0.01]) linear_extrude(0.01) offset(delta = -chamfer) arm2d();
            }
            // gusset: lofted from full clamp height to arm thickness, side edges chamfered
            hull() {
                slice(ymin, h_full);
                slice(y_gusset_end, arm_t);
            }
        }
        // keep the washer/nut area around the pivot flat
        translate([arm_x * L, eye_y, arm_t]) cylinder(r = nut_clear_r, h = h_full);
    }
}

// ---------- Clamp body of one half (local z=0 = parting plane, builds upward) ----------
// Outer face chamfered on all edges except the arm side edge, where the gusset slope continues
module top_face() {
    hull() {
        offset(delta = -chamfer) outline();
        translate([chamfer, ymin]) square([L - 2 * chamfer, 0.01]);   // arm side: matches gusset profile
    }
}
module body(h) {
    linear_extrude(h - chamfer) outline();
    if (chamfer > 0)
        hull() {
            translate([0, 0, h - chamfer]) linear_extrude(0.01) outline();
            translate([0, 0, h - 0.01])    linear_extrude(0.01) top_face();
        }
}

// ---------- Halves ----------
module half_top() {
    z0 = zs + clamp_gap/2;
    difference() {
        union() {
            translate([0, 0, z0]) body(ztop - z0);
            translate([0, 0, z0]) arm_with_gusset(ztop - z0);
        }
        linear_extrude(strut_h) slots();
        holes();
    }
}
module half_bottom() {
    z0 = zs - clamp_gap/2;
    difference() {
        union() {
            translate([0, 0, z0]) mirror([0, 0, 1]) body(z0 - zbot);
            translate([0, 0, z0]) mirror([0, 0, 1]) arm_with_gusset(z0 - zbot);
        }
        linear_extrude(strut_h) slots();
        holes();
    }
}

// ---------- Output ----------
if (part == "assembly") {
    color("orange") half_top();
    color("steelblue") half_bottom();
    %linear_extrude(strut_h) {   // struts for reference
        translate([-40, -strut_t]) square([L + 80, strut_t]);
        polygon([[-5, gap(-5)], [L + 20, gap(L + 20)],
                 [L + 20, gap(L + 20) + ptc], [-5, gap(-5) + ptc]]);
    }
} else if (part == "top") {
    translate([0, 0, -(zs + clamp_gap/2)]) half_top();
} else if (part == "bottom") {
    translate([0, 0, zs - clamp_gap/2]) rotate([180, 0, 0]) half_bottom();
} else {
    // print_plate: both halves side by side, parting plane down
    translate([0, 0, -(zs + clamp_gap/2)]) half_top();
    translate([L + 2 * eye_r + 10, 0, zs - clamp_gap/2]) rotate([180, 0, 0]) half_bottom();
}
