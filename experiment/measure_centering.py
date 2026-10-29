"""Manually mark card and inner-border corners, then calculate centering ratios."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from tkinter import Button, Canvas, Frame, Label, Tk, messagebox
from typing import Any

try:
    from .centering import MEASUREMENT_COLUMNS, calculate_centering
    from .run_experiment import read_cases
except ImportError:
    from centering import MEASUREMENT_COLUMNS, calculate_centering
    from run_experiment import read_cases


LANDMARKS = (
    ("Outer card", "top-left"),
    ("Outer card", "top-right"),
    ("Outer card", "bottom-right"),
    ("Outer card", "bottom-left"),
    ("Inner border", "top-left"),
    ("Inner border", "top-right"),
    ("Inner border", "bottom-right"),
    ("Inner border", "bottom-left"),
)


class CenteringMarker:
    """Tk interface for selecting the four outer and four inner-border corners."""

    def __init__(
        self,
        root: Tk,
        cases: list[Any],
        output_path: Path,
        completed_ids: set[str],
    ) -> None:
        try:
            from PIL import Image, ImageOps, ImageTk
        except ImportError as error:
            raise RuntimeError(
                "Pillow is required to display JPEG card images. "
                "Install dependencies with: python -m pip install -r requirements.txt"
            ) from error

        self.Image = Image
        self.ImageOps = ImageOps
        self.ImageTk = ImageTk
        self.root = root
        self.cases = cases
        self.output_path = output_path
        self.completed_ids = completed_ids
        self.skipped_ids: set[str] = set()
        self.case_index = 0
        self.points: list[tuple[float, float]] = []
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.photo = None

        root.title("Manual Pokémon Card Centering Measurement")
        self.instruction = Label(root, anchor="w", justify="left")
        self.instruction.pack(fill="x", padx=8, pady=4)
        self.canvas = Canvas(root, highlightthickness=0, cursor="crosshair")
        self.canvas.pack(padx=8)
        self.canvas.bind("<Button-1>", self.add_point)
        controls = Label(root, text="Select corners in the displayed order. Save & next validates the geometry.")
        controls.pack(pady=4)
        buttons = Frame(root)
        buttons.pack(pady=6)
        Button(buttons, text="Undo", command=self.undo).pack(side="left", padx=4)
        Button(buttons, text="Clear", command=self.clear).pack(side="left", padx=4)
        Button(buttons, text="Skip image", command=self.skip).pack(side="left", padx=4)
        Button(buttons, text="Save & next", command=self.save_and_next).pack(side="left", padx=4)
        self.show_next_case()

    def show_next_case(self) -> None:
        while self.case_index < len(self.cases):
            case = self.cases[self.case_index]
            if case.image_id not in self.completed_ids:
                break
            self.case_index += 1
        if self.case_index >= len(self.cases):
            if self.skipped_ids:
                message = (
                    f"Session finished. Saved measurements to:\n{self.output_path}\n\n"
                    f"{len(self.skipped_ids)} card(s) were skipped; rerun the tool "
                    "to measure those cards."
                )
            else:
                message = f"All cards measured. Saved measurements to:\n{self.output_path}"
            messagebox.showinfo("Centering session finished", message)
            self.root.destroy()
            return

        case = self.cases[self.case_index]
        image = self.ImageOps.exif_transpose(self.Image.open(case.image_path)).convert("RGB")
        self.original_size = image.size
        image.thumbnail((1000, 760), self.Image.Resampling.LANCZOS)
        self.scale_x = image.width / self.original_size[0]
        self.scale_y = image.height / self.original_size[1]
        self.photo = self.ImageTk.PhotoImage(image)
        self.canvas.configure(width=image.width, height=image.height)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
        self.points = []
        self.instruction.configure(
            text=(
                f"Image {self.case_index + 1}/{len(self.cases)}: {case.image_id}\n"
                "Click outer card corners clockwise from top-left, then inner printed-border "
                "corners in the same order."
            )
        )

    def add_point(self, event: Any) -> None:
        if len(self.points) >= len(LANDMARKS):
            return
        image_x = event.x / self.scale_x
        image_y = event.y / self.scale_y
        self.points.append((image_x, image_y))
        color = "red" if len(self.points) <= 4 else "cyan"
        self.canvas.create_oval(
            event.x - 4, event.y - 4, event.x + 4, event.y + 4, fill=color, outline="white"
        )
        landmark_index = len(self.points) - 1
        self.canvas.create_text(
            event.x + 8,
            event.y - 8,
            text=str(landmark_index + 1),
            fill=color,
            anchor="sw",
            font=("Segoe UI", 12, "bold"),
        )
        case_id = self.cases[self.case_index].image_id
        if len(self.points) < len(LANDMARKS):
            group, corner = LANDMARKS[len(self.points)]
            instruction = f"Next: {group} {corner}."
        else:
            instruction = "All corners selected. Choose Save & next."
        self.instruction.configure(
            text=f"{case_id}: {len(self.points)}/{len(LANDMARKS)} selected. {instruction}"
        )

    def undo(self) -> None:
        if self.points:
            self.points.pop()
            self.show_current_points()

    def clear(self) -> None:
        self.points = []
        self.show_current_points()

    def show_current_points(self) -> None:
        case = self.cases[self.case_index]
        image = self.ImageOps.exif_transpose(self.Image.open(case.image_path)).convert("RGB")
        self.original_size = image.size
        image.thumbnail((1000, 760), self.Image.Resampling.LANCZOS)
        self.scale_x = image.width / self.original_size[0]
        self.scale_y = image.height / self.original_size[1]
        self.photo = self.ImageTk.PhotoImage(image)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
        for index, (x, y) in enumerate(self.points):
            display_x = x * self.scale_x
            display_y = y * self.scale_y
            color = "red" if index < 4 else "cyan"
            self.canvas.create_oval(
                display_x - 4,
                display_y - 4,
                display_x + 4,
                display_y + 4,
                fill=color,
                outline="white",
            )
            self.canvas.create_text(
                display_x + 8,
                display_y - 8,
                text=str(index + 1),
                fill=color,
                anchor="sw",
                font=("Segoe UI", 12, "bold"),
            )
        self.instruction.configure(
            text=f"{case.image_id}: {len(self.points)}/{len(LANDMARKS)} landmarks selected."
        )

    def skip(self) -> None:
        self.skipped_ids.add(self.cases[self.case_index].image_id)
        self.case_index += 1
        self.show_next_case()

    def save_and_next(self) -> None:
        if len(self.points) != len(LANDMARKS):
            messagebox.showwarning("More points needed", "Select all eight corners, or skip this image.")
            return
        outer = tuple(self.points[:4])
        inner = tuple(self.points[4:])
        try:
            measurement = calculate_centering(outer, inner)
        except ValueError as error:
            messagebox.showerror("Invalid landmarks", str(error))
            return
        image_id = self.cases[self.case_index].image_id
        row = {
            "image_id": image_id,
            "outer_corners": json.dumps(outer, separators=(",", ":")),
            "inner_corners": json.dumps(inner, separators=(",", ":")),
            **measurement,
        }
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        write_header = not self.output_path.exists()
        with self.output_path.open("a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=MEASUREMENT_COLUMNS)
            if write_header:
                writer.writeheader()
            writer.writerow(row)
        self.completed_ids.add(image_id)
        print(
            f"Saved {image_id}: left:right {measurement['left_right_ratio']}, "
            f"top:bottom {measurement['top_bottom_ratio']}.",
            flush=True,
        )
        self.case_index += 1
        self.show_next_case()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path, default=Path("experiment/centering_measurements.csv")
    )
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    cases = read_cases(args.manifest)
    if args.output.exists() and args.overwrite:
        args.output.unlink()
    completed_ids = set()
    if args.output.exists():
        with args.output.open(newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames is None or "image_id" not in reader.fieldnames:
                raise ValueError(f"Existing output has no image_id column: {args.output}")
            completed_ids = {(row.get("image_id") or "").strip() for row in reader}
        unknown = completed_ids - {case.image_id for case in cases}
        if unknown:
            raise ValueError("Existing output contains image IDs not in the manifest.")
        print(f"Resuming: {len(completed_ids)} image measurements already saved.", flush=True)

    root = Tk()
    try:
        CenteringMarker(root, cases, args.output, completed_ids)
    except Exception:
        root.destroy()
        raise
    root.mainloop()


if __name__ == "__main__":
    main()
