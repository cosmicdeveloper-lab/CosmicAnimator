# src/cosmicanimator/interface/cli.py

"""
CosmicAnimator — Command-Line Interface

Usage
-----
Generate a Manim scene file from a JSON scenario, with optional rendering:

    python -m cosmicanimator.interface.cli --scenario work/scenario.json --out work/generated_scene.py --render

Options
-------
--scenario     Path to input scenario JSON (default: work/scenario.json)
--out          Path to output Python scene file (default: work/generated_scene.py)
--scene-class  Scene class name inside the generated file (default: Generated)
--render       If provided, immediately render with Manim after generation
"""

import argparse
from pathlib import Path
from cosmicanimator.application.generator import write_scene
from cosmicanimator.interfaces.render import render


def main() -> None:
    """Entry point for the CosmicAnimator CLI."""
    parser = argparse.ArgumentParser(description="CosmicAnimator CLI")
    parser.add_argument(
        "--scenario",
        default="work/scenario.json",
        help="Path to input scenario JSON file",
    )
    parser.add_argument(
        "--out",
        default="work/generated_scene.py",
        help="Path to output Python scene file",
    )
    parser.add_argument(
        "--scene-class",
        default="Generated",
        help="Scene class name inside the generated file",
    )
    parser.add_argument(
        "--render",
        action="store_true",
        help="If set, run Manim immediately after generation",
    )
    args = parser.parse_args()

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    write_scene(args.scenario, args.out, scene_class_name=args.scene_class)

    if args.render:
        render(args.out, args.scene_class)


if __name__ == "__main__":
    main()
