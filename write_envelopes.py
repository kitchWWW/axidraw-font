#!/usr/bin/env python3
"""Write mailing addresses on envelopes using the AxiDraw."""

import csv
import os
import sys
from dual_plotter import DualPlotter
from dual_text_lib import draw_text_line

CSV_PATH = "combined_addresses.csv"


def play_sound():
    os.system("afplay /System/Library/Sounds/Glass.aiff &")


def load_addresses():
    """Read all rows from the CSV. Returns (fieldnames, rows)."""
    with open(CSV_PATH, "r") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    return fieldnames, rows


def mark_done(name):
    """Set Done=TRUE for a name in the CSV after the plotter finishes it."""
    fieldnames, rows = load_addresses()
    for row in rows:
        if row["Name"].strip() == name.strip():
            row["Done"] = "TRUE"
    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_address_lines(row):
    """Build list of text lines from a CSV row."""
    lines = []
    name = row.get("Name", "").strip()
    if name:
        lines.append(name)
    address = row.get("Address", "").strip()
    if address:
        lines.append(address)
    line2 = row.get("Line2", "").strip()
    if line2:
        lines.append(line2)
    city_state = row.get("City State", "").strip()
    zipcode = row.get("Zip", "").strip()
    if city_state and zipcode:
        lines.append(f"{city_state} {zipcode}")
    elif city_state:
        lines.append(city_state)
    elif zipcode:
        lines.append(zipcode)
    return lines


def main():
    test_mode = "--test" in sys.argv

    # Read addresses, filter to only those not yet done
    fieldnames, addresses = load_addresses()
    todo = [a for a in addresses if a.get("Done", "").strip().upper() != "TRUE"]
    done_count = len(addresses) - len(todo)

    print(f"Loaded {len(addresses)} total addresses.")
    print(f"Already done: {done_count}, remaining: {len(todo)}")

    if not todo:
        print("Nothing to do!")
        return

    # Envelope layout
    x_offset = 2.0    # inches from left
    y_offset = 2.0    # inches from top/near edge
    line_height = 0.2  # text height in inches
    line_spacing = 0.35 # distance between line origins

    if test_mode:
        # Render a preview image of the first remaining address
        ad = DualPlotter(use_device=False)
        ad.interactive()
        ad.connect()
        lines = build_address_lines(todo[0])
        for j, line in enumerate(lines):
            draw_text_line(ad, line, x_offset, y_offset + j * line_spacing, height_in=line_height)
        ad.disconnect()
        print(f"Test mode: rendered '{todo[0]['Name']}' to image.")
        return

    # Real device mode
    ad = DualPlotter(use_device=True)
    ad.interactive()
    ad.connect()

    for i, addr in enumerate(todo):
        name = addr.get("Name", "?").strip()
        lines = build_address_lines(addr)

        print(f"\n--- Envelope {i+1}/{len(todo)}: {name} ---")
        for line in lines:
            print(f"  {line}")

        # Draw each line on the envelope
        for j, line in enumerate(lines):
            draw_text_line(ad, line, x_offset, y_offset + j * line_spacing, height_in=line_height)

        # Return pen home
        ad.moveto(0, 0)

        # Mark as done in the CSV
        mark_done(name)

        # Sound + wait (except after the last one)
        if i < len(todo) - 1:
            play_sound()
            input(f"\nDone with {name}! Load next envelope and press Enter... ")

    ad.disconnect()
    print("\nAll envelopes complete!")


if __name__ == "__main__":
    main()
