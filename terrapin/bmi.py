#! /usr/bin/env python
"""
Basic Model Interface (BMI) for a TerraPIN valley cross-section.

Wraps a single StandardTerrapin so a driver (e.g. a GRLP long-profile, one
cross-section per node) can evolve it through the CSDMS BMI: push a bed
elevation (vertical) or channel position (lateral) with set_value, call
update(), and read back the emergent valley width and the solid sediment volume
the section delivered. Each BMI instance is ONE cross-section; a reach couples
N of them independently.

Style follows gFlex's BMI: it subclasses bmipy.Bmi when available (so it
validates against the spec) and otherwise falls back to a plain object, so the
wrapper is usable without the optional bmipy dependency.

Time is nominal: TerraPIN is event-driven quasi-static geometry, so start = 0,
step = 1, end = inf, and each update() applies the queued move(s).
"""
import json

import numpy as np
from shapely.geometry import box

from terrapin.standard import StandardTerrapin

try:
    from bmipy import Bmi as _BmiBase
    _bmipy_import_error = None
except ImportError as _err:          # usable without bmipy, just not registered
    _BmiBase = object
    _bmipy_import_error = _err


class BmiStandardTerrapin(_BmiBase):
    """BMI wrapper for one TerraPIN valley cross-section (StandardTerrapin)."""

    _name = "TerraPIN valley cross-section"

    # inputs are set, then applied by update(); each also reads back the state
    _input_var_names = (
        "channel_bottom__elevation",     # target bed z_ch -> vertical sweep (incise/aggrade)
        "channel__x_position",           # target x_ch     -> migrate (the lateral driver)
    )
    _output_var_names = (
        "valley__width",                             # emergent wall-to-wall floor width
        "channel_solid_sediment__volume",            # net SOLID exported (the river's load)
        "channel_bulk_sediment__area",               # net BULK area exported
    )
    _var_units = {
        "channel_bottom__elevation": "m",
        "channel__x_position": "m",
        "valley__width": "m",
        "channel_solid_sediment__volume": "m2",      # area = volume per unit valley length
        "channel_bulk_sediment__area": "m2",
    }

    def __init__(self):
        self._model = None
        self._values = {}                # {bmi_name: 1-element float64 array}
        self._current_time = 0.0
        self._time_step = 1.0

    # ------------------------------- control --------------------------------

    def initialize(self, config_file):
        """Build the cross-section from a config (a dict, or a path to a JSON
        file with the same keys):

            {"domain": {"x_min": -120, "x_max": 120, "z_min": -70},
             "bedrock_top": -8, "surface": 0,
             "channel": {"x": 0, "width": 16, "depth": 4, "z": 0},
             "repose": {"bedrock": 75, "alluvium": 32, "colluvium": 20},
             "lambda_p": 0.35, "porosities": {"bedrock": 0.0}}
        """
        cfg = config_file if isinstance(config_file, dict) else json.load(open(config_file))
        d = cfg["domain"]
        ch = cfg["channel"]
        st = StandardTerrapin()
        st.set_bodies({
            "bedrock":  box(d["x_min"], d["z_min"], d["x_max"], cfg["bedrock_top"]),
            "alluvium": box(d["x_min"], cfg["bedrock_top"], d["x_max"], cfg["surface"]),
        })
        st.set_repose_angles(cfg["repose"])
        st.set_porosity(cfg.get("lambda_p", 0.35))
        if "porosities" in cfg:
            st.set_porosities(cfg["porosities"])
        st.set_channel_position(ch["x"])
        st.set_channel_elevation(ch.get("z", cfg["surface"]))
        st.set_channel_width(ch["width"])
        st.set_channel_depth(ch["depth"])
        st.establish_channel()
        self._model = st
        for name in self._input_var_names + self._output_var_names:
            self._values[name] = np.zeros(1)
        self._current_time = 0.0
        self._refresh()

    def _refresh(self):
        """Read the model state into the BMI value arrays."""
        m = self._model
        self._values["channel_bottom__elevation"][0] = m.z_ch
        self._values["channel__x_position"][0] = m.x_ch
        self._values["valley__width"][0] = m.compute_valley_width()
        self._values["channel_solid_sediment__volume"][0] = m.sediment_out
        self._values["channel_bulk_sediment__area"][0] = m.area_out

    def update(self):
        """Apply the queued input(s): migrate to the set x (lateral), then sweep to
        the set bed elevation (vertical). Refresh the outputs; advance nominal time.
        Do lateral and vertical in separate update()s to read each sediment flux."""
        m = self._model
        x_target = self._values["channel__x_position"][0]
        z_target = self._values["channel_bottom__elevation"][0]
        if x_target != m.x_ch:
            m.migrate(x_target)                      # lateral (Dz = 0)
        if z_target != m.z_ch:
            m.sweep(m.x_ch, z_target)                # vertical (Dx = 0)
        self._refresh()
        self._current_time += self._time_step

    def update_until(self, time):
        while self._current_time < time:
            self.update()

    def finalize(self):
        self._model = None
        self._values = {}

    # ------------------------------- info -----------------------------------

    def get_component_name(self):
        return self._name

    def get_input_item_count(self):
        return len(self._input_var_names)

    def get_output_item_count(self):
        return len(self._output_var_names)

    def get_input_var_names(self):
        return self._input_var_names

    def get_output_var_names(self):
        return self._output_var_names

    # ------------------------------- vars -----------------------------------

    def get_var_grid(self, name):
        return 0                                     # one scalar grid for the section

    def get_var_type(self, name):
        return str(self._values[name].dtype)

    def get_var_units(self, name):
        return self._var_units[name]

    def get_var_itemsize(self, name):
        return self._values[name].itemsize

    def get_var_nbytes(self, name):
        return self._values[name].nbytes

    def get_var_location(self, name):
        return "node"

    def get_value(self, name, dest):
        dest[:] = self._values[name].flat
        return dest

    def get_value_ptr(self, name):
        return self._values[name]

    def get_value_at_indices(self, name, dest, inds):
        dest[:] = self._values[name].flat[inds]
        return dest

    def set_value(self, name, src):
        self._values[name].flat[:] = src

    def set_value_at_indices(self, name, inds, src):
        self._values[name].flat[inds] = src

    # ------------------------------- time -----------------------------------

    def get_start_time(self):
        return 0.0

    def get_end_time(self):
        return float("inf")

    def get_current_time(self):
        return self._current_time

    def get_time_step(self):
        return self._time_step

    def get_time_units(self):
        return "1"                                   # nominal (event-driven)

    # ------------------------------- grid -----------------------------------
    # A single cross-section is one scalar grid (rank 0, one node).

    def get_grid_rank(self, grid):
        return 0

    def get_grid_size(self, grid):
        return 1

    def get_grid_type(self, grid):
        return "scalar"

    def get_grid_shape(self, grid, shape):
        return shape                                 # rank 0: empty

    def get_grid_node_count(self, grid):
        return 1

    def get_grid_edge_count(self, grid):
        return 0

    def get_grid_face_count(self, grid):
        return 0

    # spacing / origin: a scalar grid has neither, so return the (empty) dest
    def get_grid_spacing(self, grid, spacing):
        return spacing

    def get_grid_origin(self, grid, origin):
        return origin

    # coordinate and connectivity accessors do not apply to a scalar grid
    def get_grid_x(self, grid, x):
        raise NotImplementedError("scalar grid has no coordinates")

    def get_grid_y(self, grid, y):
        raise NotImplementedError("scalar grid has no coordinates")

    def get_grid_z(self, grid, z):
        raise NotImplementedError("scalar grid has no coordinates")

    def get_grid_edge_nodes(self, grid, edge_nodes):
        raise NotImplementedError("scalar grid has no edges")

    def get_grid_face_edges(self, grid, face_edges):
        raise NotImplementedError("scalar grid has no faces")

    def get_grid_face_nodes(self, grid, face_nodes):
        raise NotImplementedError("scalar grid has no faces")

    def get_grid_nodes_per_face(self, grid, nodes_per_face):
        raise NotImplementedError("scalar grid has no faces")
