"""Phase 3 pilot (docs/ml_plan.md): find courts in NAIP aerial photos.

Stages (run in order; each caches under data/aerial/):
  osm     fetch OSM pitch polygons + context areas for the test area (--train-area: also the training area)
  chips   read NAIP chips for training (outside Hawthorne) from Planetary Computer, and the Hawthorne mosaic
  train   fine-tune a small torchvision Faster R-CNN (MobileNetV3, BSD licence) on the chips
  mosaic  read the test-area NAIP mosaic (chips also does this)
  detect  run on the test area, score against OSM, merge boxes into sites (40 m), write docs/aerial_candidates_<area>.csv + crop PNGs

Imagery: NAIP 2022, 0.6 m, public domain, public STAC (no account). Labels: OSM leisure=pitch.
Classes: 1 racket court (tennis, pickleball, padel, ...), 2 basketball, 3 other pitch (hard negatives).
Output is a candidate list marked inferred: "court-like rectangle here, sport and access unknown".
Never written to seeds or the map. Needs .venv-aerial (see requirements-ml.txt).
"""
import argparse
import json
import math
import random
import sys
from pathlib import Path

import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # shared helpers in ingestion/
from useragent import HEADERS as UA

ROOT = Path(__file__).resolve().parent.parent.parent
CACHE = ROOT / "data" / "aerial" / "cache"
OUT = ROOT / "data" / "aerial"
SITE_GAP_M = 40      # detection boxes closer than this (edge to edge) are one site (one complex)
OVERPASS = ["https://overpass-api.de/api/interpreter", "https://z.overpass-api.de/api/interpreter"]

TRAIN_BBOX = (33.78, -118.47, 34.05, -118.22)   # south, west, north, east (LA basin around Hawthorne)
HAWTHORNE = (33.893, -118.380, 33.934, -118.318)
AREAS = {"hawthorne": HAWTHORNE}   # test areas by name; --area NAME --bbox S,W,N,E adds one
EPSG = 26911   # UTM zone of the area being worked on, set by set_zone(): 10N west of 120 W, else 11N (LA, San Diego, Las Vegas, Reno)
RES = 0.6
CHIP = 256
RACKET = {"tennis", "pickleball", "padel", "badminton", "squash", "racquetball", "paddle_tennis",
          "table_tennis", "platform_tennis", "real_tennis", "basque_pelota", "pelota"}
CLASSES = {1: "racket_court", 2: "basketball", 3: "other_pitch"}
SEED = 7


# ---------------------------------------------------------------- helpers
def overpass(q):
    import requests
    last = None
    for u in OVERPASS:
        try:
            r = requests.post(u, data={"data": q}, headers=UA, timeout=300)
            r.raise_for_status()
            return r.json()
        except Exception as e:  # try next mirror
            last = e
    raise SystemExit(f"overpass failed: {last}")


def area_of(a):
    """-> (name, bbox) for the test area chosen on the command line."""
    name = a.area
    if a.bbox:
        AREAS[name] = tuple(float(v) for v in a.bbox.split(","))
    if name not in AREAS:
        raise SystemExit(f"unknown area {name!r}: pass --bbox S,W,N,E")
    set_zone(AREAS[name])
    return name, AREAS[name]


def set_zone(bb):
    """Pick the UTM zone from the bbox centre; an area that straddles 120 W would need quads from both zones, so refuse it."""
    global EPSG
    s, w, n, e = bb
    if (w < -120 < e):
        raise SystemExit("bbox crosses 120 W (UTM zones 10N/11N): split it into one area per zone")
    EPSG = 26910 if e <= -120 else 26911


def to_utm():
    from pyproj import Transformer
    return Transformer.from_crs("EPSG:4326", f"EPSG:{EPSG}", always_xy=True)


def to_wgs():
    from pyproj import Transformer
    return Transformer.from_crs(f"EPSG:{EPSG}", "EPSG:4326", always_xy=True)


def train_files(a):
    """-> (bbox, pitches json, chips npy, chips meta, default model out) for the training area named by --train.
    The LA-basin set keeps its original file names; another region gets its own, keyed by name."""
    name = a.train
    if name == "la":
        bb = TRAIN_BBOX
        files = (OUT / "osm_pitches_train_area.json", CACHE / "train_imgs.npy", CACHE / "train_meta.json", CACHE / "model.pt")
    else:
        bbf = OUT / f"train_{name}_bbox.json"
        if getattr(a, "train_bbox", None):
            bb = tuple(float(v) for v in a.train_bbox.split(","))
        elif bbf.exists():
            bb = tuple(json.load(open(bbf)))
        else:
            raise SystemExit(f"training area {name!r}: pass --train-bbox S,W,N,E")
        files = (OUT / f"osm_pitches_train_{name}.json", CACHE / f"train_{name}_imgs.npy",
                 CACHE / f"train_{name}_meta.json", CACHE / f"model_{name}.pt")
    set_zone(bb)
    return (bb,) + files


def pitch_class(tags):
    sports = set((tags.get("sport") or "").replace(" ", "").split(";"))
    if sports & RACKET:
        return 1
    if "basketball" in sports:
        return 2
    return 3


def load_pitches(path):
    """-> list of dict(id, cls, sport, xs, ys) in UTM metres."""
    tr = to_utm()
    out = []
    for e in json.load(open(path))["elements"]:
        g = e.get("geometry")
        if not g or len(g) < 3:
            continue
        xs, ys = tr.transform([p["lon"] for p in g], [p["lat"] for p in g])
        out.append({"id": e["id"], "cls": pitch_class(e["tags"]), "sport": e["tags"].get("sport"),
                    "xs": np.array(xs), "ys": np.array(ys)})
    return out


def bbox_utm(bb):
    tr = to_utm()
    x0, y0 = tr.transform(bb[1], bb[0])
    x1, y1 = tr.transform(bb[3], bb[2])
    return min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)


def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / u if u > 0 else 0.0


# ---------------------------------------------------------------- imagery
class Naip:
    """Opens the 2022 NAIP quads covering a bbox and reads windows by UTM coordinates."""

    def __init__(self, bbox_wgs):
        import planetary_computer
        import pystac_client
        cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1",
                                        modifier=planetary_computer.sign_inplace)
        s, w, n, e = bbox_wgs
        items = list(cat.search(collections=["naip"], bbox=[w, s, e, n],
                                datetime="2022-01-01/2022-12-31", max_items=200).items())
        if not items:
            raise SystemExit("no NAIP 2022 items for bbox")
        same = [it for it in items if it.properties.get("proj:epsg", EPSG) == EPSG]
        if len(same) < len(items):
            print(f"  skipping {len(items) - len(same)} quads in another UTM zone", flush=True)
        items = same
        if not items:
            raise SystemExit("no NAIP 2022 items in this UTM zone for bbox")
        self.items = items
        self.ds = {}
        self.bounds = {}
        print(f"  {len(items)} NAIP 2022 quads", flush=True)

    def _open(self, it):
        import rasterio
        if it.id not in self.ds:
            self.ds[it.id] = rasterio.open(it.assets["image"].href)
            self.bounds[it.id] = tuple(self.ds[it.id].bounds)
        return self.ds[it.id]

    def read(self, x_ul, y_ul, w, h):
        """RGB uint8 [h,w,3] with upper-left at UTM (x_ul, y_ul), or None if no single quad holds it."""
        from rasterio.windows import Window
        x_lr, y_lr = x_ul + w * RES, y_ul - h * RES
        for it in self.items:
            ds = self._open(it)
            b = self.bounds[it.id]
            if b[0] <= x_ul and x_lr <= b[2] and b[1] <= y_lr and y_ul <= b[3]:
                row, col = ds.index(x_ul, y_ul)
                a = ds.read([1, 2, 3], window=Window(col, row, w, h))
                if a.shape != (3, h, w) or a.max() == 0:
                    return None
                return np.moveaxis(a, 0, 2)
        return None

    def mosaic(self, x0, y0, x1, y1):
        """Paste every quad overlapping the UTM box onto one canvas. -> (array, x_ul, y_ul)."""
        from rasterio.windows import Window
        w, h = int((x1 - x0) / RES), int((y1 - y0) / RES)
        canvas = np.zeros((h, w, 3), np.uint8)
        for it in self.items:
            ds = self._open(it)
            b = self.bounds[it.id]
            ox0, oy0, ox1, oy1 = max(x0, b[0]), max(y0, b[1]), min(x1, b[2]), min(y1, b[3])
            if ox0 >= ox1 or oy0 >= oy1:
                continue
            row, col = ds.index(ox0, oy1)
            ww, hh = int((ox1 - ox0) / RES), int((oy1 - oy0) / RES)
            a = np.moveaxis(ds.read([1, 2, 3], window=Window(col, row, ww, hh)), 0, 2)
            cx, cy = int((ox0 - x0) / RES), int((y1 - oy1) / RES)
            hh, ww = min(hh, h - cy, a.shape[0]), min(ww, w - cx, a.shape[1])
            if hh <= 0 or ww <= 0:
                continue
            region = canvas[cy:cy + hh, cx:cx + ww]
            patch = a[:hh, :ww]
            region[region.max(axis=2) == 0] = patch[region.max(axis=2) == 0]
        return canvas, x0, y1


def boxes_in_chip(pitches, x_ul, y_ul, w, h):
    """Pixel boxes + classes of pitches that mostly lie inside the chip."""
    boxes, labels = [], []
    for p in pitches:
        px0, px1 = (p["xs"].min() - x_ul) / RES, (p["xs"].max() - x_ul) / RES
        py0, py1 = (y_ul - p["ys"].max()) / RES, (y_ul - p["ys"].min()) / RES
        full = (px1 - px0) * (py1 - py0)
        cx0, cy0, cx1, cy1 = max(px0, 0), max(py0, 0), min(px1, w), min(py1, h)
        if cx1 <= cx0 or cy1 <= cy0 or full <= 0:
            continue
        if (cx1 - cx0) * (cy1 - cy0) < 0.6 * full or (cx1 - cx0) < 6 or (cy1 - cy0) < 6:
            continue
        boxes.append([cx0, cy0, cx1, cy1])
        labels.append(p["cls"])
    return np.array(boxes, np.float32).reshape(-1, 4), np.array(labels, np.int64)


# ---------------------------------------------------------------- stages
def stage_osm(a):
    OUT.mkdir(parents=True, exist_ok=True)
    name, (s, w, n, e) = area_of(a)
    if a.train_area:
        (ts, tw, tn, te), pitches_json, *_ = train_files(a)
        if a.train != "la":
            json.dump([ts, tw, tn, te], open(OUT / f"train_{a.train}_bbox.json", "w"))
        j = overpass(f'[out:json][timeout:240];way["leisure"="pitch"]({ts},{tw},{tn},{te});out geom tags;')
        json.dump(j, open(pitches_json, "w"))
    j = overpass(f'[out:json][timeout:120];way["leisure"="pitch"]({s},{w},{n},{e});out geom tags;')
    json.dump(j, open(OUT / f"osm_pitches_{name}.json", "w"))
    # context areas, to tell public/institutional land from the rest (private homes are never candidates)
    j = overpass(f'[out:json][timeout:120];(way["leisure"~"park|sports_centre|playground|recreation_ground|fitness_centre|golf_course"]({s},{w},{n},{e});'
                 f'way["amenity"~"school|college|university|community_centre"]({s},{w},{n},{e});'
                 f'way["landuse"~"residential"]({s},{w},{n},{e}););out geom tags;')
    json.dump(j, open(OUT / f"osm_context_{name}.json", "w"))
    print(f"osm: saved ({name})")


def stage_chips(a):
    rng = random.Random(SEED)
    CACHE.mkdir(parents=True, exist_ok=True)
    tbb, pitches_json, imgs_npy, meta_json, _ = train_files(a)
    train_epsg = EPSG
    pitches = load_pitches(pitches_json)
    name, bb = area_of(a)
    if EPSG != train_epsg:
        raise SystemExit("training area and test area are in different UTM zones")
    hx0, hy0, hx1, hy1 = bbox_utm(bb)
    pad = CHIP * RES
    inside = lambda x, y: hx0 - pad < x < hx1 + pad and hy0 - pad < y < hy1 + pad   # never train on the test area
    train = [p for p in pitches if not inside(p["xs"].mean(), p["ys"].mean())]
    by = {c: [p for p in train if p["cls"] == c] for c in (1, 2, 3)}
    rng.shuffle(by[1]); rng.shuffle(by[2]); rng.shuffle(by[3])
    picks = by[1][:a.n_racket] + by[2][:a.n_basket] + by[3][:a.n_other]
    centers = [(p["xs"].mean(), p["ys"].mean()) for p in picks]
    tx0, ty0, tx1, ty1 = bbox_utm(tbb)
    while len(centers) < len(picks) + a.n_random:
        c = (rng.uniform(tx0, tx1), rng.uniform(ty0, ty1))
        if not inside(*c):
            centers.append(c)
    naip = Naip(tbb)
    imgs, meta = [], []
    for i, (cx, cy) in enumerate(centers):
        jx, jy = rng.uniform(-40, 40) * RES, rng.uniform(-40, 40) * RES
        x_ul, y_ul = cx + jx - CHIP * RES / 2, cy + jy + CHIP * RES / 2
        try:
            im = naip.read(x_ul, y_ul, CHIP, CHIP)
        except Exception as e:
            print("  read failed:", str(e)[:80], flush=True)
            continue
        if im is None:
            continue
        imgs.append(im); meta.append((x_ul, y_ul))
        if (i + 1) % 100 == 0:
            print(f"  chips {len(imgs)}/{i + 1}", flush=True)
    np.save(imgs_npy, np.stack(imgs))
    json.dump(meta, open(meta_json, "w"))
    print(f"train chips: {len(imgs)}")
    mosaic_for(a)


def mosaic_for(a):
    """Read the test-area mosaic (own bbox, any quads) and cache it."""
    name, bb = area_of(a)
    mos, x_ul, y_ul = Naip(bb).mosaic(*bbox_utm(bb))
    np.save(CACHE / f"{name}.npy", mos)
    json.dump([x_ul, y_ul], open(CACHE / f"{name}_origin.json", "w"))
    print(f"{name} mosaic", mos.shape)


def stage_mosaic(a):
    CACHE.mkdir(parents=True, exist_ok=True)
    mosaic_for(a)


def build_model(pretrained):
    import torchvision
    from torchvision.models.detection import fasterrcnn_mobilenet_v3_large_fpn
    from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
    kw = dict(weights=None, weights_backbone=("DEFAULT" if pretrained else None),
              min_size=2 * CHIP, max_size=2 * CHIP, box_score_thresh=0.05, box_detections_per_img=100)
    m = fasterrcnn_mobilenet_v3_large_fpn(**kw)
    m.roi_heads.box_predictor = FastRCNNPredictor(m.roi_heads.box_predictor.cls_score.in_features, 4)
    return m


def augment(img, boxes):
    """Random dihedral flip/transposition. img [H,W,3], boxes [N,4] xyxy."""
    h, w = img.shape[:2]
    b = boxes.copy()
    if random.random() < 0.5:
        img = img[:, ::-1]; b[:, [0, 2]] = w - b[:, [2, 0]]
    if random.random() < 0.5:
        img = img[::-1]; b[:, [1, 3]] = h - b[:, [3, 1]]
    if random.random() < 0.5:
        img = img.transpose(1, 0, 2); b = b[:, [1, 0, 3, 2]]
    return np.ascontiguousarray(img), b


def stage_train(a):
    import torch
    torch.set_num_threads(a.threads)
    random.seed(SEED); torch.manual_seed(SEED)
    _, pitches_json, imgs_npy, meta_json, default_out = train_files(a)
    model_out = Path(a.out) if a.out else default_out
    imgs = np.load(imgs_npy)
    meta = json.load(open(meta_json))
    pitches = load_pitches(pitches_json)
    data = []
    for im, (x_ul, y_ul) in zip(imgs, meta):
        near = [p for p in pitches if abs(p["xs"].mean() - x_ul) < 400 and abs(p["ys"].mean() - y_ul) < 400]
        b, l = boxes_in_chip(near, x_ul, y_ul, CHIP, CHIP)
        data.append((im, b, l))
    n_val = max(1, len(data) // 10)
    random.shuffle(data)
    val, tr = data[:n_val], data[n_val:]
    print(f"train {len(tr)} chips, val {len(val)}; racket boxes in train: {sum((l == 1).sum() for _, _, l in tr)}")
    if a.init:   # fine-tune: start from earlier weights (e.g. the LA model) instead of the generic backbone
        model = build_model(pretrained=False)
        model.load_state_dict(torch.load(a.init))
    else:
        model = build_model(pretrained=True)
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.SGD(params, lr=a.lr, momentum=0.9, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=a.epochs)
    bs = 4
    for ep in range(a.epochs):
        model.train()
        random.shuffle(tr)
        tot = 0
        for i in range(0, len(tr), bs):
            ims, tgts = [], []
            for im, b, l in tr[i:i + bs]:
                im2, b2 = augment(im, b)
                ims.append(torch.from_numpy(im2).permute(2, 0, 1).float() / 255)
                tgts.append({"boxes": torch.from_numpy(b2).float().reshape(-1, 4), "labels": torch.from_numpy(l)})
            for g in opt.param_groups:  # short warmup
                g["lr"] = sched.get_last_lr()[0] * min(1.0, (ep * len(tr) / bs + i / bs + 1) / 50)
            loss = sum(model(ims, tgts).values())
            if not torch.isfinite(loss):
                print("  non-finite loss, skipping batch", flush=True)
                continue
            opt.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 10.0)
            opt.step()
            tot += float(loss.detach())
        sched.step()
        print(f"epoch {ep + 1}/{a.epochs} loss {tot / math.ceil(len(tr) / bs):.3f}", flush=True)
        torch.save(model.state_dict(), model_out)
    # quick chip-level check on the held-out 10% (random chips from the same area, not the Hawthorne test)
    model.eval()
    tp = fp = fn = 0
    with torch.no_grad():
        for im, b, l in val:
            out = model([torch.from_numpy(im).permute(2, 0, 1).float() / 255])[0]
            keep = (out["scores"] >= 0.5) & (out["labels"] == 1)
            det = out["boxes"][keep].numpy()
            gt = b[l == 1]
            used = set()
            for d in det:
                m = [(iou(d, g), k) for k, g in enumerate(gt) if k not in used]
                best = max(m, default=(0, -1))
                if best[0] >= 0.3:
                    tp += 1; used.add(best[1])
                else:
                    fp += 1
            fn += len(gt) - len(used)
    print(f"val chips @0.5: tp {tp} fp {fp} fn {fn}")


def nms_boxes(boxes, scores, thr=0.3):
    order = np.argsort(-scores)
    keep = []
    for i in order:
        if all(iou(boxes[i], boxes[j]) < thr for j in keep):
            keep.append(i)
    return keep


def box_gap(a, b):
    """Edge-to-edge distance between two boxes (same units as the boxes), 0 if they touch or overlap."""
    dx = max(0, max(a[0], b[0]) - min(a[2], b[2]))
    dy = max(0, max(a[1], b[1]) - min(a[3], b[3]))
    return math.hypot(dx, dy)


def cluster_sites(boxes, gap):
    """Union boxes whose edges lie within `gap` of each other. -> list of index lists (one per site)."""
    parent = list(range(len(boxes)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            if box_gap(boxes[i], boxes[j]) <= gap:
                parent[find(i)] = find(j)
    groups = {}
    for i in range(len(boxes)):
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())


PUBLIC_CTX = ("park", "recreation_ground", "playground", "sports_centre", "school", "college", "university",
              "community_centre", "fitness_centre", "golf_course")


def context_of(cx, cy, ctx):
    """Kind of the OSM area holding the point. Park/school/sports kinds win over a surrounding residential area."""
    kinds = [k for (x0, y0, x1, y1, k) in ctx if x0 <= cx <= x1 and y0 <= cy <= y1]
    for k in kinds:
        if k in PUBLIC_CTX:
            return k
    return kinds[0] if kinds else "none"


def stage_detect(a):
    import csv
    from collections import Counter
    import torch
    from PIL import Image, ImageDraw
    torch.set_num_threads(a.threads)
    name, bb = area_of(a)
    mos = np.load(CACHE / f"{name}.npy")
    x_ul, y_ul = json.load(open(CACHE / f"{name}_origin.json"))
    model = build_model(pretrained=False)
    model.load_state_dict(torch.load(a.model or CACHE / "model.pt"))
    model.eval()
    H, W = mos.shape[:2]
    step = CHIP - 48
    allb, alls, allc = [], [], []
    ntile = 0
    with torch.no_grad():
        for y in range(0, max(1, H - 48), step):
            for x in range(0, max(1, W - 48), step):
                y0, x0 = min(y, H - CHIP), min(x, W - CHIP)
                tile = mos[y0:y0 + CHIP, x0:x0 + CHIP]
                if tile.max() == 0:
                    continue
                ntile += 1
                if ntile % 200 == 0:
                    print(f"  tiles {ntile}", flush=True)
                out = model([torch.from_numpy(np.ascontiguousarray(tile)).permute(2, 0, 1).float() / 255])[0]
                for b, s, c in zip(out["boxes"].numpy(), out["scores"].numpy(), out["labels"].numpy()):
                    allb.append([b[0] + x0, b[1] + y0, b[2] + x0, b[3] + y0]); alls.append(s); allc.append(c)
    allb, alls, allc = np.array(allb).reshape(-1, 4), np.array(alls), np.array(allc)
    dets = []
    for c in (1, 2, 3):
        idx = np.where((allc == c) & (alls >= 0.2))[0]
        for k in nms_boxes(allb[idx], alls[idx]):
            dets.append((allb[idx][k], float(alls[idx][k]), c))
    print(f"tiles {ntile}; raw detections kept: {len(dets)}")

    gt = []
    for p in load_pitches(OUT / f"osm_pitches_{name}.json"):
        gt.append(([(p["xs"].min() - x_ul) / RES, (y_ul - p["ys"].max()) / RES,
                    (p["xs"].max() - x_ul) / RES, (y_ul - p["ys"].min()) / RES], p["cls"], p["sport"]))
    # only OSM pitches inside the mosaic can be scored
    gt = [g for g in gt if 0 <= (g[0][0] + g[0][2]) / 2 <= W and 0 <= (g[0][1] + g[0][3]) / 2 <= H]
    gt_r = [g for g in gt if g[1] == 1]
    print(f"OSM pitches in area: {len(gt)}; racket courts: {len(gt_r)} {dict(Counter(g[2] for g in gt_r))}")
    by_sport = {}

    gap_px = SITE_GAP_M / RES
    osites = cluster_sites([g[0] for g in gt_r], gap_px)
    res = {}
    for thr in (0.3, 0.5, 0.7, 0.9):
        d = [x for x in dets if x[2] == 1 and x[1] >= thr]
        used, tp = set(), 0
        for box, s, _ in sorted(d, key=lambda t: -t[1]):
            m = max(((iou(box, g[0]), k) for k, g in enumerate(gt_r) if k not in used), default=(0, -1))
            if m[0] >= 0.3:
                tp += 1; used.add(m[1])
        if thr == 0.5:   # recall by sport: do the misses sit in pickleball (small, often painted on tennis courts)?
            for k, g in enumerate(gt_r):
                s = by_sport.setdefault(g[2] or "?", [0, 0])
                s[1] += 1
                s[0] += k in used
        # site level: a detected site is right if one of its boxes overlaps an OSM court; an OSM site is found if any of its courts is overlapped
        dsites = cluster_sites([x[0] for x in d], gap_px)
        d_hit = sum(any(iou(d[i][0], g[0]) >= 0.1 for i in grp for g in gt_r) for grp in dsites)
        o_hit = sum(any(iou(gt_r[i][0], x[0]) >= 0.1 for i in grp for x in d) for grp in osites)
        res[thr] = {"boxes": len(d), "matched_osm": tp, "osm_courts": len(gt_r), "det_sites": len(dsites),
                    "det_sites_on_osm": d_hit, "osm_sites": len(osites), "osm_sites_found": o_hit}
        print(f"score>={thr}: boxes {len(d)}, matched OSM {tp} (precision vs OSM {tp / max(1, len(d)):.2f}, recall {tp / max(1, len(gt_r)):.2f}); "
              f"sites: detected {len(dsites)}, on OSM courts {d_hit}; OSM sites {len(osites)}, found {o_hit}")

    print("recall @0.5 by OSM sport tag: " + ", ".join(f"{k} {v[0]}/{v[1]}" for k, v in sorted(by_sport.items())))
    res["recall_by_sport_0.5"] = by_sport

    # candidates: racket detections on no OSM pitch of any kind, merged into one row per site
    ctx = []
    tr = to_utm()
    for e in json.load(open(OUT / f"osm_context_{name}.json"))["elements"]:
        g = e.get("geometry")
        if g and len(g) >= 3:
            xs, ys = tr.transform([p["lon"] for p in g], [p["lat"] for p in g])
            kind = e["tags"].get("leisure") or e["tags"].get("amenity") or e["tags"].get("landuse")
            ctx.append((min(xs), min(ys), max(xs), max(ys), kind))
    known = [(p["xs"].mean(), p["ys"].mean()) for p in load_pitches(OUT / f"osm_pitches_{name}.json") if p["cls"] == 1]  # mapped racket courts in this area
    to_ll = to_wgs()
    cand = [d for d in dets if d[2] == 1 and d[1] >= a.min_score and not any(iou(d[0], g[0]) >= 0.1 for g in gt)]
    rows, groups = [], []
    for grp in cluster_sites([c[0] for c in cand], gap_px):
        bx = np.array([cand[i][0] for i in grp])
        x0, y0, x1, y1 = bx[:, 0].min(), bx[:, 1].min(), bx[:, 2].max(), bx[:, 3].max()
        cx, cy = x_ul + (x0 + x1) / 2 * RES, y_ul - (y0 + y1) / 2 * RES
        lon, lat = to_ll.transform(cx, cy)
        near = min((math.hypot(cx - kx, cy - ky) for kx, ky in known), default=None)
        where = context_of(cx, cy, ctx)
        rows.append({"lat": round(lat, 6), "lon": round(lon, 6), "n_boxes": len(grp),
                     "max_score": round(max(cand[i][1] for i in grp), 3),
                     "extent_long_m": round(max(x1 - x0, y1 - y0) * RES, 1), "extent_short_m": round(min(x1 - x0, y1 - y0) * RES, 1),
                     "osm_context": where, "nearest_osm_court_m": "" if near is None else round(near),
                     "review_note": ("in a mapped park/school/sports area: check the operator's public page" if where in PUBLIC_CTX else
                                     "not in a mapped park/school (residential or unmapped land): may be a private yard, HOA or resort court, do NOT add to OSM without a public source"),
                     "status": "inferred", "sport": "unknown", "access": "unknown"})
        groups.append((bx, (x0, y0, x1, y1)))
    if a.context_only:   # residential/unmapped candidates are mostly private yards or HOAs
        keep = [i for i, r in enumerate(rows) if r["osm_context"] in PUBLIC_CTX]
        print(f"--context-only: {len(keep)} of {len(rows)} sites are in a mapped park/school/sports area")
        rows, groups = [rows[i] for i in keep], [groups[i] for i in keep]
    order = sorted(range(len(rows)), key=lambda i: -rows[i]["max_score"])
    rows, groups = [rows[i] for i in order], [groups[i] for i in order]
    crops = CACHE / f"crops_{name}"
    crops.mkdir(exist_ok=True)
    for old in crops.glob("*.png"):
        old.unlink()
    img = Image.fromarray(mos)
    for i, (r, (bx, (x0, y0, x1, y1))) in enumerate(zip(rows, groups), 1):
        r["site_id"] = f"{name}-{i:03d}"
        pad = 40
        ox, oy = int(max(0, x0 - pad)), int(max(0, y0 - pad))
        crop = img.crop((ox, oy, int(min(W, x1 + pad)), int(min(H, y1 + pad))))
        dr = ImageDraw.Draw(crop)
        for b in bx:
            dr.rectangle([b[0] - ox, b[1] - oy, b[2] - ox, b[3] - oy], outline=(255, 0, 0))
        crop.save(crops / f"{r['site_id']}.png")
    out_csv = ROOT / "docs" / f"aerial_candidates_{name}.csv"
    out_csv.parent.mkdir(exist_ok=True)
    cols = ["site_id", "lat", "lon", "n_boxes", "max_score", "extent_long_m", "extent_short_m", "osm_context",
            "nearest_osm_court_m", "review_note", "status", "sport", "access"]
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        wr.writeheader(); wr.writerows(rows)
    print(f"candidate sites (score>={a.min_score}, on no OSM pitch): {len(rows)} from {len(cand)} boxes -> {out_csv}")
    json.dump(res, open(OUT / f"{name}_eval.json", "w"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="stage", required=True)
    o = sp.add_parser("osm"); o.set_defaults(f=stage_osm)
    o.add_argument("--train-area", action="store_true", help="also fetch the training pitches (--train NAME)")
    m = sp.add_parser("mosaic"); m.set_defaults(f=stage_mosaic)
    c = sp.add_parser("chips"); c.set_defaults(f=stage_chips)
    c.add_argument("--n-racket", type=int, default=450); c.add_argument("--n-basket", type=int, default=120)
    c.add_argument("--n-other", type=int, default=100); c.add_argument("--n-random", type=int, default=150)
    t = sp.add_parser("train"); t.set_defaults(f=stage_train)
    t.add_argument("--epochs", type=int, default=8); t.add_argument("--threads", type=int, default=8)
    t.add_argument("--init", help="weights to fine-tune from (e.g. data/aerial/cache/model.pt, the LA model); use a lower --lr")
    t.add_argument("--lr", type=float, default=0.003)
    t.add_argument("--out", help="weights file to write (default model.pt for la, else model_<train>.pt)")
    for q in (sp.choices["osm"], c, t):
        q.add_argument("--train", default="la", help="training-area name; la = the LA basin (built in), another name needs --train-bbox S,W,N,E once")
        q.add_argument("--train-bbox", help="S,W,N,E of a new training area (WGS84)")
    d = sp.add_parser("detect"); d.set_defaults(f=stage_detect)
    d.add_argument("--threads", type=int, default=8); d.add_argument("--min-score", type=float, default=0.5)
    d.add_argument("--model", help="weights file (default data/aerial/cache/model.pt)")
    d.add_argument("--context-only", action="store_true", help="keep only candidates inside a mapped park/school/sports area")
    for q in (sp.choices["osm"], sp.choices["mosaic"], c, d):
        q.add_argument("--area", default="hawthorne", help="test-area name (files are keyed by it)")
        q.add_argument("--bbox", help="S,W,N,E of the test area (WGS84); built-in for hawthorne")
    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    sys.exit(main())
