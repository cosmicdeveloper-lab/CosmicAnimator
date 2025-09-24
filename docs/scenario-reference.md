
# CosmicAnimator Scenario JSON — Reference (Valid Markdown)

This document defines the **valid JSON shapes** your generator accepts and **introduces every action and transition** currently supported by the runtime. Examples below are **copy‑pasteable JSON** (no comments).

---

## 1) Top‑Level Forms

A scenario   **object with `script`**.



### B. Object form
```json
{
  "script": [
    {
      "line": "Welcome to CosmicAnimator!",
      "action": "render_title",
      "args": {"text": "CosmicAnimator"}
    }
  ]
}
```

---

## 2) Step Object

Each step may include a narration `line` and either **one** `action` with `args` **or** multiple `actions` (array executed in order).

```json
{
  "line": "This step narrates and shows a title.",
  "action": "render_title",
  "args": {"text": "Hello!"}
}
```

```json
{
  "line": "Do several things in order.",
  "actions": [
    {"name": "layout_boxes"},
    {"name": "apply_transition", "args": {"name": "highlight_shapes", "target_ids": ["box2"]}}
  ]
}
```

### Fields
- **`line`** (string, optional) — Narration. If present and no explicit `narrate` action is included, narration is **implicit** for this step (via your voice service).
- **`action`** (string, optional) — Single action name (see registry below).
- **`args`** (object, optional) — Parameters for `action`.
- **`actions`** (array, optional) — Multiple actions, as `{ "name": "...", "args": { ... } }` entries.

> Targets by ID refer to shapes stored in the internal scene store (`ActionContext.store`).

---

## 3) Actions — Complete Reference

Below is the canonical list of actions exposed by the current generator. (If you add new actions in code, append them here to keep the README in sync.)

### 3.1 `render_title`
Renders a prominent HUD title.
```json
{"name": "render_title", "args": {
  "text": "CosmicAnimator",
  "variant": "title",
  "color": "accent",
  "font_size": 72
}}
```
**Args**
- `text` (str, required)
- `variant` (str, optional, e.g. `"title"`)
- `color` (role/hex, optional)
- `font_size` (int, optional)

---

### 3.2 `layout_boxes`
Creates a row/column/grid of labeled boxes. Stores each box under a **deterministic ID** (see `id_from_labels` and `id_prefix`).

```json
{"name": "layout_boxes", "args": {
  "count": 3,
  "labels": ["Process A", "Process B", "Process C"],
  "direction": "row",
  "filled": true
}}
```
**Args**
- `count` (int, required unless `labels` provided) — number of boxes
- `labels` (array[str], optional) — if provided and `id_from_labels=true`, IDs are **slugified** labels (e.g., `"Process B"` → `"process_b"`)
- `direction` (str, optional: `"row"` | `"column"`)
- `rows`, `cols` (int, optional) — for grid layouts
- `filled` (bool, optional) — fill shapes instead of outline only
- `appear` (bool, optional) — animate appearance
- `appear_direction` (str, optional) — e.g., `"up"`, `"down"`, `"left"`, `"right"`

**Resulting IDs**
- `box1`, `box2`, `box3`

---

### 3.3 `layout_branch`
Root → children diagram with connectors.
```json
{"name": "layout_branch", "args": {
  "root_label": "Server",
  "child_labels": ["API", "DB", "Cache"],
  "direction": "row",
  "spacing": 1.0,
  "level_gap": 1.4
}}
```
**Args**
- `root_label` (str, optional; default `"Root"`)
- `child_labels` (array[str], required)
- `direction` (str, optional)
- `spacing`, `level_gap` (float, optional)

**IDs**
- Root: `root` (or custom via `id`)
- Children: slugified labels or `node1..nodeN`

---

### 3.4 `render_loop`
Draws an orbit/loop arrow around a target.
```json
{"name": "render_loop", "args": {
  "target_id": "box1",
  "span_degrees": 300,
  "revolutions": 1,
  "run_time": 1.2
}}
```
**Args**
- `target_id` (str, required)
- `span_degrees` (float, optional, default `360`)
- `revolutions` (float, optional, default `1`)
- `run_time` (float, optional)

---


### 3.5 `apply_transition`
Apply a **single transition** or a **pipeline** to one/many targets by ID.

**Single transition**
```json
{"name": "apply_transition", "args": {
  "name": "ghost_shapes",
  "target_ids": ["box2"],
  "run_time": 0.8
}}
```

**Pipeline**
```json
{"name": "apply_transition", "args": {
  "pipeline": [
    {"name": "ripple_effect"},
    {"name": "highlight_shapes", "args": {"color": "accent"}}
  ],
  "target_ids": ["box2"]
}}
```

**Args (shared)**
- `target_ids` (array[str], required for most transitions)
- `transition` (str, required if not using `pipeline`)
- `pipeline` (array[TransitionSpec], required if not using `transition`)
- `run_time` (float, optional, default depends on transition)
- `lag_ratio` (float, optional, for groups)

---

## 4) Transitions — Complete Reference

The following names are recognized by `apply_transition`. Each transition supports the generic timing args (`run_time`, `lag_ratio`, `ease`) unless noted otherwise.

### 4.1 `highlight_shapes`
Temporarily highlight one or more shapes with overlays (fill, glow, or both).

**Args**
- `color` (str, default `"auto"`) — theme role, hex, or `"auto"` (per-part)
- `mode` (str, default `"both"`) — `"fill"`, `"glow"`, or `"both"`
- `fill_opacity` (float, default `0.60`)
- `scale` (float, default `1.04`) — slight enlargement
- `include_text` (bool, default `false`)
- `in_time` (float, default `0.28`)
- `hold_time` (float, default `0.55`)
- `out_time` (float, default `0.30`)
- `lag_ratio` (float, default `0.08`)
- `pulse` (bool, default `false`)
- `pulse_times` (int, default `2`)
- `pulse_scale` (float, default `1.06`)
- `pulse_period` (float, default `0.35`)

---

### 4.2 `focus_on_shape`
Dim everything except the given targets, lifting them visually.

**Args**
- `include_text` (bool, default `true`)
- `backdrop_role` (str, default `"#000000"`) — fill color for backdrop
- `backdrop_opacity` (float, default `0.62`)
- `in_time` (float, default `0.35`)
- `hold_time` (float, default `0.60`)
- `out_time` (float, default `0.30`)
- `lag_ratio` (float, default `0.0`)

---

### 4.3 `ghost_shapes`
Temporarily dim stroke layers, then restore.

**Args**
- `dim_opacity` (float, default `0.1`)
- `run_time` (float, default `0.6`)
- `pause_ratio` (float, default `0.12`)
- `rate_func` (callable, optional)
- `min_stroke` (float, default `0.2`)
- `exclude_filled` (bool, default `false`)

---

### 4.4 `orbit_around`
Orbit an object around a point or another object.

**Args**
- `center` (array, optional) — explicit orbit center
- `around` (VMobject, optional) — orbit around another object
- `radius` (float, optional)
- `start_angle` (float, optional)
- `rotations` (float, default `1.0`)
- `clockwise` (bool, default `false`)
- `run_time` (float, default `2.0`)
- `rate_func` (callable, default `linear`)
- `rotate_self` (bool, default `false`)

---

### 4.5 `shake`
Shake an object with optional color flash.

**Args**
- `amplitude` (float, default `0.3`)
- `shakes` (int, default `2`)
- `run_time` (float, default `0.6`)
- `axis` (str, default `"horizontal"`) — `"horizontal"` | `"vertical"`
- `color_change` (bool, default `true`)
- `color` (Manim color, default `RED`)

---

### 4.6 `ripple_effect`
Concentric rings expanding/contracting from targets.

**Args**
- `color` (str, default `"auto"`)
- `rings` (int, default `3`)
- `ring_gap` (float, default `0.25`)
- `stroke_width` (float, default `4.0`)
- `base_opacity` (float, default `0.9`)
- `from_edge` (bool, default `true`)
- `center_override` (array, optional)
- `inward` (bool, default `false`)
- `fade_in` (bool, default `false`)
- `fade_out` (bool, default `true`)
- `in_time` (float, default `0.10`)
- `expand_time` (float, default `0.8`)
- `hold_time` (float, default `0.0`)
- `out_time` (float, default `0.25`)
- `ring_lag` (float, default `0.12`)
- `target_lag` (float, default `0.05`)

---

### 4.7 `zoom_to`
Zoom camera frame to a target, hold, then optionally restore.

**Args**
- `zoom` (float, default `1.8`) — factor (>1 zooms in)
- `in_time` (float, default `0.9`)
- `hold_time` (float, default `0.5`)
- `out_time` (float, default `0.8`)
- `rate_func` (callable, default `smooth`)

---

### 4.8 `zoom_out`
Zoom out from current view, hold, then optionally restore.

**Args**
- `zoom` (float, default `1.8`)
- `in_time` (float, default `0.9`)
- `hold_time` (float, default `0.5`)
- `out_time` (float, default `0.8`)
- `rate_func` (callable, default `smooth`)

---

### 4.9 `pan_to`
Pan camera center smoothly toward a target.

**Args**
- `run_time` (float, default `1.0`)
- `rate_func` (callable, default `smooth`)
- `direction_step` (float, default `2.0`)
- `direction` (str, default `"left"`) — `"left"`, `"right"`, `"up"`, `"down"`


## 5) IDs & Targeting — Rules

- Most layout actions store created objects under IDs:
  - Default pattern: `box1`, `box2`, ...
- Use these IDs with `target_ids` in `apply_transition` and other actions needing a target.

---

## 6) Validated Example
```json
{
  "script": [
    {
      "line": "Welcome to CosmicAnimator!",
      "actions": [
        {
          "name": "render_title",
          "args": {
            "text": "CosmicAnimator",
            "color": "accent"
          }
        }
      ]
    },
    {
      "line": "Here are three processes. Highlight the middle process.",
      "actions": [
        {
          "name": "layout_boxes",
          "args": {
            "count": 3,
            "labels": ["Process A", "Process B", "Process C"],
            "direction": "row",
            "filled": true
          }
        },
        {
          "name": "apply_transition",
          "args": {
            "pipeline": [
              {"name": "highlight_shapes", "args": {"color": "accent"}}
            ],
            "target_ids": ["box2"]
          }
        }
      ]
    }
  ]
}
```

This will create IDs `box1`, `box2`, `box3`, so the transition can reliably target `"box2"`.
