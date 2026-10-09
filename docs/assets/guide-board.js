// Full-board renderer adapted from board.js: the same JointJS components and libavoid routes.
// The companion owns navigation and saved progress; this renderer owns only its drawing.
(() => {
  const BASE = new URL('vendor/libavoid/', document.currentScript.src).href;
  let library;
  const cachedRoutes = new Map();
  function ready() {
    if (!library) library = import(BASE + 'index.js').then(async ({AvoidLib}) => {
      await AvoidLib.load(BASE + 'libavoid.wasm');
      return AvoidLib.getInstance();
    });
    return library;
  }
  window.mountGuideBoard = function(root, D, options) {
    if (!window.joint) { root.textContent = 'Board renderer unavailable. Use the connection list below.'; return {destroy(){}, zoom(){}, fit(){}}; }
    let disposed = false;
  const { dia, shapes } = joint;
  const W = 1360, H = 860;
  const FONT = "system-ui, Segoe UI, Helvetica, Arial, sans-serif";
  const WIRE = { WH: ["#ffffff", "#334155"], BU: ["#2563eb", "#1e3a8a"], BN: ["#92400e", "#451a03"],
                 BK: ["#1f2937", "#000000"], GY: ["#9ca3af", "#4b5563"], DIODE: ["#d1d5db", "#111827"] };
  const CORE = { BN: "#92400e", BU: "#2563eb", BK: "#111827" };
  const PIN_TEXT = { "-": "−" };
  const STYLE = {
    socket: { fill: "#1f2937", stroke: "#1f2937" }, box: { fill: "#f1f5f9", stroke: "#17202a" },
    diode: { fill: "#111827", stroke: "#111827" }, wago: { fill: "#f1f5f9", stroke: "#64748b" },
    plug: { fill: "#1f2937", stroke: "#1f2937" }, sensor: { fill: "#e8f5ec", stroke: "#15803d" },
  };

  const Area = dia.Element.define("autolever.Area", {
    attrs: { body: { width: "calc(w)", height: "calc(h)", rx: 12, fill: "#f8fafc", strokeWidth: 1.5, strokeDasharray: "6 5" } },
  }, { markup: [{ tagName: "rect", selector: "body" }] });
  // area titles are their own elements, so the router keeps wires off them
  const Caption = dia.Element.define("autolever.Caption", {
    attrs: { label: { x: 0, y: 14, fontSize: 14, fontWeight: 700, fontFamily: FONT, stroke: "#ffffff", strokeWidth: 4, paintOrder: "stroke" } },
  }, { markup: [{ tagName: "text", selector: "label" }] });

  const Part = dia.Element.define("autolever.Part", {
    attrs: {
      body: { width: "calc(w)", height: "calc(h)", rx: 6, strokeWidth: 1.5 },
      title: { x: "calc(0.5*w)", y: -10, textAnchor: "middle", fontSize: 14, fontWeight: 800, fill: "#17202a", fontFamily: FONT },
      sub: { x: "calc(0.5*w)", y: "calc(h+17)", textAnchor: "middle", fontSize: 11.5, fontWeight: 600, fill: "#5b6672", fontFamily: FONT },
    },
  }, { markup: [{ tagName: "rect", selector: "body" }, { tagName: "rect", selector: "band" },
               { tagName: "text", selector: "title" }, { tagName: "text", selector: "sub" }] });

  const ns = { ...shapes, autolever: { Area, Part, Caption } };
  const graph = new dia.Graph({}, { cellNamespace: ns });
  const holder = document.createElement("div");
  const paper = new dia.Paper({
    el: holder, model: graph, width: W, height: H, cellViewNamespace: ns, interactive: false,
    background: { color: "#ffffff" }, async: false,
    labelsLayer: true,   // wire numbers above the parts, never hidden under a terminal
  });

  // ---- board: areas (frame: false = a zone title inside another area), decorative props, parts with their terminals
  for (const [key, a] of Object.entries(D.areas)) {
    const frame = a.frame !== false;
    // z below the wires (5.5): frames and titles never cover them
    if (frame) graph.addCell(new Area({ id: "area-" + key, z: 1, position: { x: a.at[0], y: a.at[1] }, size: { width: a.size[0], height: a.size[1] },
      attrs: { body: { stroke: a.color } } }));
    graph.addCell(new Caption({ id: "caption-" + key, z: 2, position: { x: a.at[0] + (frame ? 14 : 0), y: a.at[1] + (frame ? 10 : 0) },
      size: { width: a.title.length * 8, height: 18 }, attrs: { label: { text: a.title, fill: a.color } } }));
    for (const [x, name] of a.glands || []) graph.addCell(new Caption({ id: "gland-" + name, z: 2, position: { x: x + 26, y: a.at[1] - 9 },
      size: { width: 22, height: 18 }, attrs: { label: { text: name, fill: a.color, fontSize: 12 } } }));
  }
  D.props.forEach((p, i) => graph.addCell(new shapes.standard.Rectangle({
    id: "prop-" + i, position: { x: p.at[0], y: p.at[1] }, size: { width: p.size[0], height: p.size[1] },
    attrs: { body: { fill: "#e5e7eb", stroke: "#475569", rx: 4 }, label: { text: p.name, fontSize: 12, fontWeight: 600, fill: "#475569", fontFamily: FONT } },
  })));

  for (const [id, p] of Object.entries(D.parts)) {
    const inset = p.kind === "socket" ? 17 : 0;
    const groups = {}, items = [];
    for (const [side, pins] of Object.entries(p.ports)) {
      const args = { left: { dx: inset }, right: { dx: -inset }, top: { dy: 0 }, bottom: { dy: p.kind === "box" ? -16 : 0 } }[side];
      groups[side] = { position: { name: side, args } };
      for (const pin of pins) {
        const core = p.kind === "sensor" ? CORE[pin] : null;
        items.push({
          id: pin, group: side,
          markup: [{ tagName: "circle", selector: "pb" }, { tagName: "text", selector: "pt" }],
          attrs: {
            pb: core ? { r: 6, fill: core, stroke: core } : { r: 9.5, fill: "#e5e7eb", stroke: "#9ca3af", strokeWidth: 1 },
            pt: { text: core ? "" : (PIN_TEXT[pin] || pin), textAnchor: "middle", y: 3.6, fontSize: pin.length > 2 ? 8.5 : 10,
                  fontWeight: 700, fill: "#475569", fontFamily: FONT, pointerEvents: "none" },
          },
        });
      }
    }
    const style = p.kind === "button" ? { fill: p.color, stroke: "#9ca3af", rx: p.size[0] / 2 } : STYLE[p.kind];
    graph.addCell(new Part({
      id, position: { x: p.at[0], y: p.at[1] }, size: { width: p.size[0], height: p.size[1] },
      ports: { groups, items },
      attrs: { body: style, title: { text: p.name }, sub: { text: p.sub || "" },
               // the silver ring of a diode, on the K (ring) side
               band: p.kind === "diode" ? { x: "calc(w-14)", y: 0, width: 7, height: "calc(h)", fill: "#d1d5db" } : { display: "none" } },
    }));
  }

  // ---- routing with libavoid: orthogonal wires around the parts, parallel wires nudged apart

  const DIR = { top: 1, bottom: 2, left: 4, right: 8 };   // libavoid ConnDirFlags
  // every part as a rectangle including its title above and label below, with its terminals as pins;
  // terminal circles sit on the part edge, so that side is padded and no wire runs across a terminal
  const obstacles = graph.getElements().filter((el) => el.get("type") !== "autolever.Area").map((el) => {
    const b = el.getBBox(), part = D.parts[el.id] || {};
    const pad = (side) => (part.ports?.[side] && part.kind !== "socket" ? 14 : 0);
    const y0 = b.y - Math.max(part.name ? 22 : 0, pad("top")), y1 = b.y + b.height + Math.max(part.sub ? 22 : 0, pad("bottom"));
    const x0 = b.x - pad("left"), x1 = b.x + b.width + pad("right");
    const pins = [];
    for (const [side, names] of Object.entries(part.ports || {})) {
      const pos = el.getPortsPositions(side);
      for (const pin of names) {
        const ox = { left: 0, right: x1 - x0 }[side] ?? b.x - x0 + pos[pin].x;
        const oy = { top: 0, bottom: y1 - y0 }[side] ?? b.y + pos[pin].y - y0;
        pins.push({ key: el.id + ":" + pin, ox, oy, dir: DIR[side] });
      }
    }
    return { id: el.id, x0, y0, x1, y1, pins };
  });
  // the walls of a box with glands: wires leave it only through the gaps, as in the real box, and
  // tall fences between the glands outside keep each cable in its own gland's channel
  for (const [key, a] of Object.entries(D.areas)) {
    if (!a.glands) continue;
    const [x0, y0] = a.at, x1 = x0 + a.size[0], y1 = y0 + a.size[1], t = 4, gap = 22;
    const wall = (xa, ya, xb, yb) => obstacles.push({ id: "wall-" + key + obstacles.length, x0: xa, y0: ya, x1: xb, y1: yb, pins: [] });
    const gx = a.glands.map((g) => g[0]).sort((p, q) => p - q);
    let x = x0 - t;
    for (const g of gx) { wall(x, y0 - t, g - gap, y0 + t); x = g + gap; }
    wall(x, y0 - t, x1 + t, y0 + t); wall(x0 - t, y1 - t, x1 + t, y1 + t); wall(x0 - t, y0 - t, x0 + t, y1 + t); wall(x1 - t, y0 - t, x1 + t, y1 + t);
    for (let i = 1; i < gx.length; i++) { const m = (gx[i - 1] + gx[i]) / 2; wall(m - 2, -5000, m + 2, y0); }
  }

  function route(Avoid, wires) {
    const param = (n) => Avoid.RoutingParameter[n], option = (n) => Avoid.RoutingOption[n];
    const r = new Avoid.Router(Avoid.RouterFlag.OrthogonalRouting.value);
    r.setRoutingParameter(param("shapeBufferDistance"), 8);
    r.setRoutingParameter(param("idealNudgingDistance"), 9);
    r.setRoutingParameter(param("segmentPenalty"), 40);
    r.setRoutingParameter(param("crossingPenalty"), 200);
    r.setRoutingOption(option("nudgeOrthogonalSegmentsConnectedToShapes"), true);
    r.setRoutingOption(option("nudgeSharedPathsWithCommonEndPoint"), true);
    r.setRoutingOption(option("performUnifyingNudgingPreprocessingStep"), true);
    const shapeOf = {}, pinOf = {};
    let cls = 1;
    for (const o of obstacles) {
      const shape = new Avoid.ShapeRef(r, new Avoid.Rectangle(new Avoid.Point(o.x0, o.y0), new Avoid.Point(o.x1, o.y1)));
      shapeOf[o.id] = shape;
      for (const p of o.pins) {
        const pin = new Avoid.ShapeConnectionPin(shape, cls, p.ox / (o.x1 - o.x0), p.oy / (o.y1 - o.y0), true, 0, p.dir);
        pin.setExclusive(false);   // a terminal may take two wires
        pinOf[p.key] = cls++;
      }
    }
    const end = (e) => new Avoid.ConnEnd(shapeOf[e.split(":")[0]], pinOf[e]);
    const conns = wires.map((w) => new Avoid.ConnRef(r, end(w.a), end(w.b)));
    r.processTransaction();
    const routes = conns.map((c) => {
      const pl = c.displayRoute(), pts = [];
      for (let i = 0; i < pl.size(); i++) pts.push({ x: pl.at(i).x, y: pl.at(i).y });
      return pts;
    });
    r.delete();
    return routes;
  }


  function diodeVertices(id, sourcePin, targetPin) {
    const part=D.parts[id], el=graph.getCell(id);
    const sideOf=pin=>Object.keys(part.ports).find(side=>part.ports[side].includes(pin));
    const pos=pin=>{const p=el.getPortsPositions(sideOf(pin))[pin];return {x:part.at[0]+p.x,y:part.at[1]+p.y};};
    const source=pos(sourcePin), target=pos(targetPin);
    const top=part.at[1]-(part.kind==='socket'?34:45);
    if(part.kind==='socket') return [{x:part.at[0]+part.size[0]+14,y:source.y},{x:part.at[0]+part.size[0]+14,y:top},{x:part.at[0]-14,y:top},{x:part.at[0]-14,y:target.y}];
    // pins facing down (valve plugs): the diode hangs just below the part, across its two pins
    const y=sideOf(sourcePin)==='bottom'?part.at[1]+part.size[1]+36:top;
    return [{x:source.x,y},{x:target.x,y}];
  }
  function wireLink(w, i, vertices) {
    const [pa, a] = [w.a.split(":")[0], w.a.slice(w.a.indexOf(":") + 1)];
    const [pb, b] = [w.b.split(":")[0], w.b.slice(w.b.indexOf(":") + 1)];
    const c = WIRE[w.col];
    const link = new shapes.standard.DoubleLink({
      id: "w" + w.no, source: { id: pa, port: a }, target: { id: pb, port: b },
      z: 5.5,   // above the area frames, below the parts: terminal numbers stay readable
      vertices: w.col === 'DIODE' ? diodeVertices(pa, a, b) : vertices,
      connector: { name: "rounded", args: { radius: 8 } },
      attrs: { line: { stroke: c[0], strokeWidth: 4, targetMarker: { type: "path", d: "" } },
               outline: { stroke: c[1], strokeWidth: 7 } },
      labels: [{
        position: [0.5, 0.35, 0.65][i % 3],
        markup: [{ tagName: "rect", selector: "pill" }, { tagName: "text", selector: "num" }],
        attrs: {
          num: { text: w.no, fontSize: 12, fontWeight: 800, fill: "#17202a", fontFamily: FONT, textAnchor: "middle", textVerticalAnchor: "middle" },
          pill: { ref: "num", x: "calc(x-7)", y: "calc(y-3)", width: "calc(w+14)", height: "calc(h+6)", rx: 9, ry: 9,
                  fill: "#ffffff", stroke: c[1], strokeWidth: 1.5 },
        },
      }],
    });
    if (w.col === "DIODE") {   // draw the part itself: black body, silver ring towards the source (+) end
      link.attr({ line: { stroke: "#9ca3af", strokeWidth: 3 }, outline: { stroke: "#4b5563", strokeWidth: 5 } });
      link.labels([{
        position: { distance: 0.5, args: { keepGradient: true, ensureLegibility: false } },
        markup: [{ tagName: "rect", selector: "body" }, { tagName: "rect", selector: "ring" }],
        attrs: {
          body: { x: -17, y: -8, width: 34, height: 16, rx: 4, fill: "#111827" },
          ring: { x: -13, y: -8, width: 6, height: 16, fill: "#d1d5db" },
        },
      }, {   // the name stays upright, just beside the body (above it when the diode hangs below a part)
        position: { distance: 0.5, offset: D.parts[pa].ports.bottom?.includes(a) ? -18 : 18 },
        markup: [{ tagName: "text", selector: "name" }],
        attrs: { name: { text: w.no, fontSize: 13, fontWeight: 800, fill: "#17202a", fontFamily: FONT, textAnchor: "middle", textVerticalAnchor: "middle" } },
      }]);
    }
    return link;
  }


  root.appendChild(holder);
  root.setAttribute('aria-label', 'Full wiring board. Select a numbered wire or diode to inspect it.');
  const all = D.steps.flatMap(s => s.wires);
  const step = D.steps[options.step];
  const selected = step.wires[options.wire];
  const visible = options.scope === 'all' ? all : options.scope === 'single' ? [selected] : step.wires;
  const wires = visible;
  const used = new Set(visible.flatMap(w => [w.a.split(':')[0], w.b.split(':')[0]]));
  const terms = new Set([selected.a, selected.b]);
  for (const [id,p] of Object.entries(D.parts)) {
    const el = graph.getCell(id);
    el.attr('root/opacity', used.has(id) ? 1 : .65);
    for (const port of el.getPorts()) {
      if (terms.has(id+':'+port.id)) {
        el.portProp(port.id, 'attrs/pb', {fill:'#e1f7df',stroke:'#237b33',strokeWidth:3});
        el.portProp(port.id, 'attrs/pt/fill', '#173d23');
      }
    }
  }
  const links = {};
  function highlight(no, hot) {
    const l = links[no];
    if (!l) return;
    l.attr('outline/strokeWidth', hot ? 11 : (l.get('diode') ? 5 : 7));
    l.attr('outline/stroke', hot ? '#198b47' : WIRE[l.get('color')][1]);
  }
  const key = wires.map(w => w.no).join(',');
  ready().then(Avoid => {
    if (disposed) return;
    if (!cachedRoutes.has(key)) cachedRoutes.set(key, route(Avoid, wires));
    const routes = cachedRoutes.get(key);
    const placed = [];   // wire numbers already on the board: the next one picks a free spot along its wire
    wires.forEach((w,i) => {
      const l = wireLink(w,i,routes[i]);
      l.set({color:w.col, diode:w.col === 'DIODE'});
      links[w.no] = l;
      graph.addCell(l);
      if (w.col !== 'DIODE') {
        const v = paper.findViewByModel(l);
        const r = [.5, .35, .65, .2, .8].find(r => { const p = v.getPointAtRatio(r); return placed.every(q => Math.abs(q.x - p.x) > 26 || Math.abs(q.y - p.y) > 18); }) ?? .5;
        l.label(0, { position: r });
        placed.push(v.getPointAtRatio(r));
      }
      // Keep terminal labels readable. Diode bands are on the source/cathode side.
      const view = paper.findViewByModel(l);
      if (view) {
        view.el.dataset.connection = w.no;
        view.el.setAttribute('role','button');
        view.el.setAttribute('tabindex','0');
        view.el.setAttribute('aria-label', w.no + ': ' + w.la + ' to ' + w.lb + (w.col==='DIODE' ? '; ring at '+w.la : ''));
        view.el.addEventListener('keydown', event => {
          if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); options.select(w.no); }
        });
      }
    });
    highlight(selected.no,true);
    root.dataset.ready = 'true';
  }).catch(error => {
    if (disposed) return;
    const note=document.createElement('p');note.className='ag-board-error';
    note.textContent='Wire router unavailable. Use the labelled connection list below.';root.appendChild(note);
    root.dataset.ready='error';
  });
  paper.on('link:mouseenter', view => highlight(view.model.id.slice(1),true));
  paper.on('link:mouseleave', view => highlight(view.model.id.slice(1),view.model.id === 'w'+selected.no));
  paper.on('link:pointerclick', view => options.select(view.model.id.slice(1)));
  let zoomFactor = options.zoom || 1;
  function fit() {
    if (disposed) return;
    const scale = Math.min(root.clientWidth / W, root.clientHeight / H) * zoomFactor;
    paper.setDimensions(W * scale, H * scale);
    paper.scale(scale);
  }
  const observer = new ResizeObserver(fit);observer.observe(root);fit();
  // printing: the whole board at page width
  const beforePrint = () => { const s = Math.min(700 / W, 700 / H); paper.setDimensions(W * s, H * s); paper.scale(s); };
  addEventListener('beforeprint', beforePrint); addEventListener('afterprint', fit);
  // Mouse/pen dragging pans the zoomed canvas. Touch scrolling stays native.
  let drag;
  root.addEventListener('pointerdown', event => {
    if (event.pointerType==='touch' || event.target.closest('.joint-link')) return;   // wires and their numbers stay clickable
    drag={x:event.clientX,y:event.clientY,left:root.scrollLeft,top:root.scrollTop};
    root.setPointerCapture(event.pointerId);
  });
  root.addEventListener('pointermove', event => {
    if (!drag) return;
    root.scrollLeft=drag.left+drag.x-event.clientX;root.scrollTop=drag.top+drag.y-event.clientY;
  });
  root.addEventListener('pointerup',()=>{drag=null;});
  root.addEventListener('pointercancel',()=>{drag=null;});
  return {
    destroy(){ disposed=true;observer.disconnect();removeEventListener('beforeprint',beforePrint);removeEventListener('afterprint',fit);paper.remove();graph.clear(); },
    zoom(value){zoomFactor=value;fit();},
    fit(){zoomFactor=1;fit();root.scrollTo(0,0);},
    highlight
  };
  };
})();
