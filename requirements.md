Totally—here’s a clean spec you can hand to a dev/designer.
(If you actually meant “videos,” note these are **print** graphics; specs below are for large-format print.)

# Exhibit Graphics — Production Requirements

## Deliverables

1. **Backwall graphic**

   * **Trim size:** 100 × 217 cm (1000 × 2170 mm)
   * **Bleed:** +5 mm on all sides → **Document size with bleed:** 1010 × 2180 mm
   * **Orientation:** Portrait

2. **Counter graphic**

   * **Trim size:** 30 × 80 cm (300 × 800 mm)
   * **Bleed:** +5 mm on all sides → **Document size with bleed:** 310 × 810 mm
   * **Orientation:** Portrait

## Layout rules

* **Safe area (both pieces):** keep all text/logos **≥50 mm** inside from every trimmed edge.
* **Backwall “no-text” zone:** a **30 × 80 cm** rectangle **flush to the bottom-left corner** of the trim area. Background color/pattern may continue here, but **no copy or logos**.
* The event manual shows the full wall as 244 cm tall with a 27 cm structural/header zone. Your **printable artwork is 217 cm high**—design within that height.

## Color & imagery

* **Color mode:** **CMYK** (no RGB/spot/Pantone unless agreed with printer).
* **Rich black (if needed):** C60 M40 Y40 K100 (or printer’s preferred recipe).
* **Images/photos:** embedded (no links), **150–300 dpi at full size** (≥150 dpi minimum for large format).
* Avoid neon/very saturated RGB colors; they won’t reproduce in CMYK.

## Type & vectors

* **All text must be converted to outlines** (a.k.a. curves/paths).
* Prefer vector elements for logos/shapes; only use raster where necessary.

## File format & export

* **Primary delivery:** **PDF (Print)**, one PDF per piece.

  * Include **crop/trim marks** and **5 mm bleed**.
  * Do **not** downsample below 150 dpi.
* **If the organizer insists on AI/EPS:** provide AI/EPS with fonts outlined and all images embedded. (Printers can convert from your PDF if needed.)

## Naming & packaging

* `Backwall_100x217cm_bleed5mm_CMYK.pdf`
* `Counter_30x80cm_bleed5mm_CMYK.pdf`
* Include small **JPG proofs** for quick review. Zip everything in a single folder.

---

## Programmer-friendly geometry (mm; origin = **bottom-left** of the **trim** area)

```json
{
  "units": "mm",
  "backwall": {
    "trim": { "width": 1000, "height": 2170 },
    "bleed": { "all_sides": 5 },
    "safe_inset": 50,
    "no_text_zone": { "x": 0, "y": 0, "width": 300, "height": 800 }
  },
  "counter": {
    "trim": { "width": 300, "height": 800 },
    "bleed": { "all_sides": 5 },
    "safe_inset": 50
  },
  "print": {
    "color_mode": "CMYK",
    "min_effective_dpi": 150,
    "preferred_effective_dpi": 300,
    "rich_black": { "C": 60, "M": 40, "Y": 40, "K": 100 },
    "outline_all_text": true,
    "embed_images": true,
    "deliver_as_pdf_with_crop_marks_and_bleed": true
  }
}
```

---

## Pre-flight checklist (both pieces)

* [ ] Canvas set to **trim size** + **5 mm bleed** on all sides
* [ ] **CMYK** document; no spot/Pantone unless approved
* [ ] All text **outlined**; all images **embedded**
* [ ] **Safe area** respected; **no-text zone** on backwall respected
* [ ] Effective image resolution **≥150 dpi** at final size
* [ ] Exported **PDF (Print)** with **crop marks & bleed**

If you want, I can also supply blank PDF/AI templates matching these specs (with bleed/safe/no-text guides) so the dev can place content programmatically.
