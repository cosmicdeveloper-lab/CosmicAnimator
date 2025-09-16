
# CosmicAnimator Scenario JSON — Reference (Valid Markdown)

This document defines the **valid JSON shapes** your generator accepts and **introduces every action and transition** currently supported by the runtime. Examples below are **copy‑pasteable JSON** (no comments).

---

## 1) Top‑Level Forms

A scenario can be either a **list of steps** or an **object with `script`**. Both are equivalent.

### A. Array form
```json
[
  {"line": "Welcome to CosmicAnimator!"},
  {"action": "render_title", "args": {"text": "CosmicAnimator"}}
]
```

### B. Object form
```json
{
  "script": [
    {"line": "Welcome to CosmicAnimator!"},
    {"action": "render_title", "args": {"text": "CosmicAnimator"}}
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
    {"name": "render_title", "args": {"text": "Pipeline"}},
    {"name": "apply_transition", "args": {"transition": "fade_in", "target_ids": ["title"]}}
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
  "font_size": 72,
  "id": "title"
}}
```
**Args**
- `text` (str, required)
- `variant` (str, optional, e.g. `"title"`, `"subtitle"`)
- `color` (role/hex, optional)
- `font_size` (int, optional)
- `id` (str, optional) — Explicit ID to reference later

---

### 3.2 `layout_boxes`
Creates a row/column/grid of labeled boxes. Stores each box under a **deterministic ID** (see `id_from_labels` and `id_prefix`).

```json
{"name": "layout_boxes", "args": {
  "count": 3,
  "labels": ["Process A", "Process B", "Process C"],
  "direction": "row",
  "filled": true,
  "id_from_labels": true,
  "id_prefix": ""
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
- `id_prefix` (str, optional, default `"box"`) — if **not** using `id_from_labels`, generated IDs are `"{id_prefix}1"`, `"{id_prefix}2"`, ...
- `id_from_labels` (bool, optional, default `false`) — when `true`, IDs are slugified labels

**Resulting IDs**
- With `id_from_labels=true`: `process_a`, `process_b`, `process_c`
- Otherwise (default): `box1`, `box2`, `box3`

---

### 3.3 `layout_branch`
Root → children diagram with connectors.
```json
{"name": "layout_branch", "args": {
  "root_label": "Server",
  "child_labels": ["API", "DB", "Cache"],
  "direction": "row",
  "spacing": 1.0,
  "level_gap": 1.4,
  "id_from_labels": true,
  "id_prefix": "node"
}}
```
**Args**
- `root_label` (str, optional; default `"Root"`)
- `child_labels` (array[str], required)
- `direction` (str, optional)
- `spacing`, `level_gap` (float, optional)
- `id_from_labels`, `id_prefix` — same behavior as in `layout_boxes`

**IDs**
- Root: `root` (or custom via `id`)
- Children: slugified labels or `node1..nodeN`

---

### 3.4 `render_loop`
Draws an orbit/loop arrow around a target.
```json
{"name": "render_loop", "args": {
  "target_id": "process_b",
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

### 3.5 `voice_config`
Configure the voice service (Coqui).
```json
{"name": "voice_config", "args": {
  "service": "coqui",
  "model": "tts_models/en/vctk/vits",
  "speaker_idx": "p231"
}}
```
**Args**
- `service` (str, optional; currently `"coqui"`)
- `model` (str, optional)
- `speaker_idx` (str/int, optional; e.g., `"p231"`) — takes precedence over defaults

---

### 3.6 `narrate`
Speak a line immediately (useful when you **don’t** want to rely on implicit `line` narration).
```json
{"name": "narrate", "args": {
  "text": "Here are three processes.",
  "add_subtitles": true
}}
```
**Args**
- `text` (str, required)
- `add_subtitles` (bool, optional, default `true`)

---

### 3.7 `apply_transition`
Apply a **single transition** or a **pipeline** to one/many targets by ID.

**Single transition**
```json
{"name": "apply_transition", "args": {
  "transition": "fade_in",
  "target_ids": ["process_b"],
  "run_time": 0.8
}}
```

**Pipeline**
```json
{"name": "apply_transition", "args": {
  "pipeline": [
    {"name": "slide_in", "args": {"direction": "up"}},
    {"name": "highlight_shapes", "args": {"color": "accent"}}
  ],
  "target_ids": ["process_b"]
}}
```

**Args (shared)**
- `target_ids` (array[str], required for most transitions)
- `transition` (str, required if not using `pipeline`)
- `pipeline` (array[TransitionSpec], required if not using `transition`)
- `run_time` (float, optional, default depends on transition)
- `lag_ratio` (float, optional, for groups)
- `ease` (str, optional; e.g., `"smooth"`, `"ease_in_out"`) — if supported

---

## 4) Transitions — Complete Reference

The following names are recognized by `apply_transition`. Each transition supports the generic timing args (`run_time`, `lag_ratio`, `ease`) unless noted otherwise.

### 4.1 `highlight_shapes`
Visually emphasize one or more targets (stroke width/glow bump; optional color shift).
```json
{"name": "highlight_shapes", "args": {
  "color": "accent",
  "glow": true,
  "stroke_scale": 1.4
}}
```

### 4.2 `ghost_shapes`
Dim/out‑of‑focus effect for non‑targets, preserving target emphasis.
```json
{"name": "ghost_shapes", "args": {
  "opacity": 0.15,
  "non_targets": "dim"
}}
```

### 4.3 `fade_in`
Fade targets from 0 → 1 opacity.
```json
{"name": "fade_in", "args": {}}
```

### 4.4 `fade_out`
Fade targets from 1 → 0 opacity.
```json
{"name": "fade_out", "args": {}}
```

### 4.5 `slide_in`
Translate from an off‑screen direction.
```json
{"name": "slide_in", "args": {
  "direction": "up",
  "distance": 1.0
}}
```

### 4.6 `slide_out`
Translate off‑screen.
```json
{"name": "slide_out", "args": {
  "direction": "down",
  "distance": 1.0
}}
```

### 4.7 `pulse`
Scale up/down briefly (good for attention cues).
```json
{"name": "pulse", "args": {
  "scale": 1.1
}}
```

### 4.8 `ripple`
Concentric ripple from target center (visual emphasis).
```json
{"name": "ripple", "args": {
  "rings": 3
}}
```

> If a transition is missing in code, either add it to your transition registry or remove it here to keep this doc authoritative.

---

## 5) IDs & Targeting — Rules

- Most layout actions store created objects under IDs:
  - Default pattern: `box1`, `box2`, ...
  - With `id_prefix`: `process_1`, `process_2`, ...
  - With `id_from_labels=true`: slugified labels, e.g. `"Process B"` → `process_b`
- Use these IDs with `target_ids` in `apply_transition` and other actions needing a target.

---

## 6) Validated Example (Targets by Label → Slug)

Your provided JSON is valid; to make `"process_b"` target exist deterministically, enable `id_from_labels` in `layout_boxes`:

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
            "color": "accent",
            "id": "title"
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
            "filled": true,
            "id_from_labels": true
          }
        },
        {
          "name": "apply_transition",
          "args": {
            "pipeline": [
              {"name": "highlight_shapes", "args": {"color": "accent"}}
            ],
            "target_ids": ["process_b"]
          }
        }
      ]
    }
  ]
}
```

This will create IDs `process_a`, `process_b`, `process_c`, so the transition can reliably target `"process_b"`.

---

## 7) Action & Transition Registry (Summary Table)

| Type | Name | Key Args |
|---|---|---|
| Action | render_title | text, color, font_size, id |
| Action | layout_boxes | count, labels, direction, filled, id_from_labels, id_prefix |
| Action | layout_branch | root_label, child_labels, direction, spacing, level_gap |
| Action | render_loop | target_id, span_degrees, revolutions, run_time |
| Action | voice_config | service, model, speaker_idx |
| Action | narrate | text, add_subtitles |
| Action | apply_transition | transition **or** pipeline, target_ids, run_time |
| Transition | highlight_shapes | color, glow, stroke_scale |
| Transition | ghost_shapes | opacity, non_targets |
| Transition | fade_in | — |
| Transition | fade_out | — |
| Transition | slide_in | direction, distance |
| Transition | slide_out | direction, distance |
| Transition | pulse | scale |
| Transition | ripple | rings |

---
