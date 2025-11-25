# CosmicAnimator

![Project Banner](docs/banner.png)

A theme-aware, Manim-based animation generator for short-form, neon-styled technical diagrams, with optional text-to-speech narration and on-video subtitles.

## ✨ Features

- **Theme system**: central palette/roles/strokes/glow/typography via `core/constants.py` and friends.
- **Style helpers**: Composable styling for shapes, text, and arrows (`adapters/style/*`).
- **Transitions**: Motion, fades, highlights, cameras, visuals, timing (`adapters/transitions/*`).
- **Narration**: TTS orchestration with optional subtitle overlay (`application/narration/*`).
- **Actions**: Declarative building blocks with a simple registry (`application/actions/*`).
- **Generator**: Produce a self-contained Manim scene from a JSON scenario (`application/generator.py`).

---

## 🏗 Project Architecture
[View Mermaid Diagram](docs/mermaid.md)

---

## 🚀 Quick Start

### 1) Build the environment 

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
```

### 2) Install

```bash
pip install -e .
```

> You’ll also need FFmpeg for Manim renders.


### 3) Build .env

```bash
AZURE_SUBSCRIPTION_KEY=YOUR_KEY
AZURE_SERVICE_REGION=YOUR_REGION
```


### 4) Prepare a work/ directory

```bash
mkdir work
echo '{}' > work/scenario.json
```

### 5) Generate a scene from JSON

```bash
cosmicanimator --scenario work/scenario.json --out work/generated_scene.py --render
```
Higher quality 👇🏻
```bash
cosmicanimator --scenario work/scenario.json --out work/generated_scene.py --render -qh or -qm
```

---

## 🧪 Tests

`tests/` covers fast unit checks, integration wiring, and a light end-to-end import:

Run with:

```bash
pytest -q
```

---

## 📜 Scenario JSON Reference

See:
- [Scenario Reference (Markdown)](docs/scenario-reference.md)

---

## 🤝 Contributing

1. Fork and create a feature branch.
2. Keep actions **pure** (return animations; do not call `scene.play` inside actions).
3. Prefer **theme-aware** helpers from `adapters/style` and `adapters/transitions`.
4. Add/extend tests under `tests/`.
5. Use descriptive docstrings and type hints.
6. Conventional commits encouraged.

---

## 🗺 Module Guide

- `core/` — declarative entities and theme wrapper.
- `adapters/style/` — style helpers for text, shapes, arrows.
- `adapters/transitions/` — visual effects.
- `application/narration/` — TTS + subtitles orchestration.
- `application/actions/` — actions registry and concrete actions.
- `application/generator.py` — JSON/entity → scene file.
- `interfaces/` — render + CLI wrappers.

---

## 🎬 Samples & Showcase

Here’s a quick preview of what CosmicAnimator generates:

![Sample Animation](docs/sample.gif)

For more sample animations and behind-the-scenes content, visit my socials:  

- [Instagram](https://www.instagram.com/_cosmicdeveloper?igsh=MW9rem41aG9sNjhmdg%3D%3D&utm_source=qr)  
- [YouTube](https://youtube.com/@cosmic.developer?si=nRzi9DqhKmy_86Yl)  

---

## 🪐 License

- CosmicAnimator © 2025 by Benyamin Amini
- Licensed under Creative Commons Attribution–NonCommercial 4.0 (CC BY-NC 4.0).

- ✔️ Free for personal, educational, and non-commercial use
- ✔️ Attribution required (“Made with CosmicAnimator by Benyamin Amini”)
- ❌ Commercial use, monetized content, or redistribution requires permission
- For commercial or institutional licensing, contact: cosmicdeveloper.b@gmail.com