# CosmicAnimator Scenario JSON — Reference

This document defines the **valid JSON structure** accepted by the CosmicAnimator engine.  
It serves as a complete **authoring guide** for writing scenario files passed to the runtime.

Every example shown below is **valid JSON** and can be copy‑pasted directly into your scenario file.

---

## Table of Contents

1. [Top‑Level Structure](#1-top-level-structure)
2. [Step Object](#2-step-object)
3. [Actions Reference](#3-actions-reference)
   - [render_title](#31-render_title)
   - [layout_boxes](#32-layout_boxes)
   - [layout_branch](#33-layout_branch)
   - [apply_transition](#34-apply_transition)
4. [Transitions Reference](#4-transitions-reference)
   - [shine](#41-shine)
   - [spin](#42-spin)
   - [blackhole](#43-blackhole)
   - [hawking_radiation](#44-hawking_radiation)
   - [shooting_star](#45-shooting_star)
   - [pulsar](#46-pulsar)
5. [ID Targeting Rules](#5-id-targeting-rules)
6. [Complete Example](#6-complete-example)

---

## 1) Top‑Level Structure

A scenario file is a **JSON object** with a single top-level field: `script`.

### Example

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

Each step in `script` represents one moment in the animation timeline.

It may include a **narration line** and either:
- one `action` with `args`, or  
- multiple `actions` (executed sequentially).

### Example (single action)

```json
{
  "line": "This step narrates and shows a title.",
  "action": "render_title",
  "args": {"text": "Hello!"}
}
```

### Example (multiple actions)

```json
{
  "line": "Do several things in order.",
  "actions": [
    {"name": "layout_boxes"},
    {"name": "apply_transition", "args": {"name": "shine", "target_ids": ["box2"]}}
  ]
}
```

### Fields

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| `line` | string | optional | Narration text. If no explicit `narrate` action is present, narration is implicit. |
| `action` | string | optional | Name of a single action to perform. |
| `args` | object | optional | Arguments for the `action`. |
| `actions` | array | optional | List of `{ "name": "...", "args": { ... } }` objects executed sequentially. |

> Targets in `args` refer to shapes stored in the internal scene store (`ActionContext.store`).

---

## 3) Actions Reference

### 3.1 `render_title`

Renders a styled **HUD title** using theme-aware typography.  
Appears with a short **fade-in** animation at the top of the frame.

```json
{"name": "render_title", "args": {
  "text": "Understanding Async vs Sync",
  "color": "primary",
  "font_size": 72,
  "variant": "title",
  "margin": 4,
  "center": true
}}
```

**Args**

| Name | Type | Default | Description |
|------|------|----------|-------------|
| `text` | str | — | Title text content. |
| `color` | str | `None` | Text/stroke color (theme default if `None`). |
| `font_size` | float | `None` | Font size override. |
| `variant` | str | `"title"` | Style variant key for `style_text`. |
| `style_kwargs` | dict | `None` | Extra style options. |
| `margin` | float | `4` | Vertical offset from top edge. |
| `center` | bool | `false` | Horizontally center the title. |

---

### 3.2 `layout_boxes`

Creates a **row**, **column**, or **grid** of labeled shapes, optionally connected by arrows or lines.

```json
{"name": "layout_boxes", "args": {
  "count": 3,
  "labels": ["Process A", "Process B", "Process C"],
  "direction": "row",
  "connection_type": "arrow",
  "arrow_color": "muted",
  "filled": true,
  "label_position": "down"
}}
```

**Args**

| Name | Type | Default | Description |
|------|------|----------|-------------|
| `shape` | str | `"square"` | Shape type (from registry). |
| `size` | float | — | Shape size. |
| `count` | int | `3` | Number of shapes. |
| `labels` | list[str] | `None` | Labels under/above shapes. |
| `label_color` | str | `None` | Label text color. |
| `direction` | str | `"row"` | `"row"`, `"column"`, or `"grid"`. |
| `rows`, `cols` | int | — | Used when `direction="grid"`. |
| `spacing` | float | `1.2` | Gap between shapes. |
| `color` | str | `"primary"` | Base color. |
| `filled` | bool | `false` | Fill shapes with color. |
| `connection_type` | str | `None` | `"arrow"`, `"line"`, or `"curved_arrow"`. |
| `arrow_color` | str | `"muted"` | Connector color. |
| `connection_labels` | list[str] | `None` | Optional connector labels. |
| `label_position` | str | `"down"` | `"up"`, `"down"`, `"left"`, `"right"`. |
| `center_at` | tuple | `(0,0,0)` | Center position. |

**Resulting IDs:** `shape1`, `shape2`, `connector1`, …

---

### 3.3 `layout_branch`

Creates a **branch diagram** connecting a **root node** to multiple **child nodes**.

```json
{"name": "layout_branch", "args": {
  "root_label": "Main Concept",
  "child_labels": ["Part A", "Part B", "Part C"],
  "direction": "down",
  "connection_type": "arrow",
  "root_color": "primary",
  "child_color": "secondary",
  "arrow_color": "muted"
}}
```

**Args**

| Name | Type | Default | Description |
|------|------|----------|-------------|
| `root_shape` | str | `"circle"` | Shape for the root node. |
| `child_shape` | str | `"square"` | Shape for child nodes. |
| `child_count` | int | `3` | Number of child nodes. |
| `direction` | str | `"down"` | `"up"`, `"down"`, `"left"`, `"right"`. |
| `spacing` | float | `1.2` | Gap between children. |
| `level_gap` | float | `1.5` | Distance between root and children. |
| `root_label` | str | `""` | Root label text. |
| `child_labels` | list[str] | `None` | Labels for child nodes. |
| `root_color` | str | `"primary"` | Color for root node. |
| `child_color` | str | `"secondary"` | Color for child nodes. |
| `connection_type` | str | `"arrow"` | `"arrow"` or `"line"`. |
| `center_at` | tuple | `(0,0,0)` | Center position of layout. |

**Resulting IDs:** `root`, `child1`, `child2`, `arrow1`, …

---

### 3.4 `apply_transition`

Applies one or more **visual transitions** to shapes or groups.


**Args**

| Name | Type | Description |
|------|------|--------------|
| `transition` | str | Single transition to apply. |
| `args` | dict | Arguments for that transition. |
| `pipeline` | list[dict] | Sequence of transitions to chain. |
| `target_ids` | list[str] | IDs of stored objects to target. |
| `target_id` | str | Shortcut for one target. |

---

## 4) Transitions Reference

### 4.1 `shine`

Creates a **pulsing glow** around targets using transparent bands.

```json
{
  "name": "apply_transition",
  "args": {
    "pipeline": [
      {
        "name": "shine"
      }
    ],
    "target_ids": [
      "shape1",
      "shape2"
    ]
  }
}
```

### 4.2 `spin`

Rotates one or more targets continuously for a fixed duration.

```json
{
  "name": "apply_transition",
  "args": {
    "pipeline": [
      {
        "name": "spin"
      }
    ],
    "target_ids": [
      "shape1",
      "shape2"
    ]
  }
}
```

### 4.3 `blackhole`

A **cosmic collapse** transition pulling the targets into a spinning horizon.

```json
{
  "name": "apply_transition",
  "args": {
    "pipeline": [
      {
        "name": "blackhole"
      }
    ],
    "target_ids": [
      "shape1",
      "shape2"
    ]
  }
}
```

### 4.4 `hawking_radiation`

Simulates **energy emission** from a fading targets.

```json
{
  "name": "apply_transition",
  "args": {
    "pipeline": [
      {
        "name": "hawking_radiation"
      }
    ],
    "target_ids": [
      "shape1",
      "shape2"
    ]
  }
}
```

### 4.5 `shooting_star`

A **cinematic streak** crossing the scene — ideal for title reveals.

```json
{"name": "apply_transition", "args": {
  "name": "shooting_star"
}}
```

### 4.6 `pulsar`

Creates **DNA‑like glowing strands** around a target.

```json
{
  "name": "apply_transition",
  "args": {
    "pipeline": [
      {
        "name": "blackhole"
      }
    ],
    "target_id": "shape1"
  }
}
```

---

## 5) ID Targeting Rules

- Most layout actions automatically assign IDs to created shapes.  
- Use these IDs in later steps for transitions or further modifications.

| Action | ID Pattern |
|---------|-------------|
| `layout_boxes` | `shape1`, `shape2`, `connector1`, … |
| `layout_branch` | `root`, `child1`, `arrow1`, … |

Example usage:

```json
{
  "name": "apply_transition",
  "args": {
    "pipeline": [
      {
        "name": "blackhole"
      }
    ],
    "target_ids": [
      "shape1",
      "shape2"
    ]
  }
}
```

---

## 6) Complete Example

```json
{
  "script": [
    {
      "line": "Welcome to CosmicAnimator!",
      "actions": [
        {"name": "render_title", "args": {"text": "CosmicAnimator"}}
      ]
    },
    {
      "line": "Here are three processes.",
      "actions": [
        {"name": "layout_boxes", "args": {"labels": ["Process A", "Process B", "Process C"]}},
        {"name": "apply_transition", "args": {"pipeline": [{"name": "blackhole"}], "target_id": "shape2"}}
      ]
    }
  ]
}
```

This will create IDs `shape1`, `shape2`, `shape3`, allowing transitions to target them directly.

---
