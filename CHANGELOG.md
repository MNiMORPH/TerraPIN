# Changelog

All notable changes to TerraPIN are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project aims to
follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Standard model (`StandardTerrapin`)** — the mobile-channel model: two one-wall
  units sharing a channel that moves across the valley floor, producing asymmetric
  valleys, channel belts, buried paleochannels, and dated terraces. Operations:
  `incise`, `aggrade`, `migrate` (lateral planation, with an optional at-capacity
  channel belt), and `avulse` (a discontinuous hop that preserves the vacated belt).
- **Unified `sweep(x1, z1)`** — the one channel-motion primitive of which `incise`,
  `migrate`, and `aggrade` are special cases; it reads erode-vs-deposit from the
  geometry. A diagonal sweep (lateral planation *while* incising) leaves a **sloped
  strath** — the strath-terrace-forming process the discrete ops could only step.
- **`retreat(side, dx)`** — the first **hillslope** process: a valley wall retreats
  parallel and sheds **talus** (colluvium) at its base, burying it as the apron
  grows. The river-absent counterpart to the channel's fluvial work.
- **Per-body porosity (`lambda_p`)** — each body converts bulk area to a **solid**
  sediment volume, `area * (1 - lambda_p)` (bedrock 0; alluvium/colluvium 0.35;
  overridable via `set_porosities`). `sediment_out` is now the net **solid**
  exported (a river's load); `area_out` is the net bulk area.
- **`StandardTerrapin.compute_valley_width()`** — emergent, asymmetric, wall-to-wall
  (floor deposits do not narrow it).
- **BMI wrapper** — `terrapin.bmi.BmiStandardTerrapin` drives one cross-section
  through the CSDMS Basic Model Interface; a `[bmi]` optional extra pulls `bmipy`.
- **Body coalescing** — contiguous bodies that share all attributes (kind,
  lithology, age, porosity) merge into one polygon; with ages tracked this gives a
  litho+chronostratigraphy, without them a lithostratigraphy.
- **Shared plotting module** (`terrapin.plotting`), used by both models and the
  examples.
- Examples reorganized into `examples/symmetric/` and `examples/standard/`, with
  talus demos (`talus_slope_retreat.py`, `talus_valley.py`).

## [0.1.0] - 2026-07-23

First release of the rewritten library. The geometry core is now polygon algebra
on Shapely/GEOS, and TerraPIN is organized as a driver-agnostic geometry and
mass-balance engine.

### Changed
- Rewrote the geometry core as **polygon algebra** on Shapely/GEOS, replacing the
  legacy hand-rolled line-intersection and point-classification model. Mass
  conservation is now structural (eroded area = deposited area = sediment out).
- Ported the code to **Python 3 / NumPy 2**.

### Added
- **`Terrapin` state object** — a driver-agnostic engine told what happened
  (`incise`, `aggrade`, `plane_laterally`) that returns updated geometry and a
  mass balance, plus `compute_valley_width()` and `plot()`.
- **Material-following repose walls** — failure walls bend at each material
  contact, with a per-lithology angle of repose.
- **Colluvial-pile (talus) placement** via a PLIC volume-conservation solver.
- **Terrace and provenance tracking** — deposits carry their deposition age,
  surfaces their abandonment age; `terraces()` reads the stranded benches from
  the live geometry and reports each terrace's age (its abandonment).
- Runtime dependency declarations, a modern `pyproject.toml` build, and PyPI
  packaging; a pytest suite; worked examples and an architecture document.

### Removed
- The legacy line-intersection model and the Python-2 `ez_setup` build bootstrap.

[Unreleased]: https://github.com/MNiMORPH/TerraPIN/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/MNiMORPH/TerraPIN/compare/v0.0.0...v0.1.0
