#! /usr/bin/env python
"""Tests for the BMI wrapper of a TerraPIN cross-section (terrapin.bmi)."""
import numpy as np
import pytest

pytest.importorskip("shapely")
pytest.importorskip("scipy")

from terrapin.bmi import BmiStandardTerrapin

CONFIG = {
    "domain": {"x_min": -120, "x_max": 120, "z_min": -70},
    "bedrock_top": -8, "surface": 0,
    "channel": {"x": 0, "width": 16, "depth": 4, "z": 0},
    "repose": {"bedrock": 75, "alluvium": 32, "colluvium": 20},
    "lambda_p": 0.35,
}


def make():
    b = BmiStandardTerrapin()
    b.initialize(dict(CONFIG))
    return b


def one(b, name):
    return b.get_value(name, np.zeros(1))[0]


def test_initialize_and_metadata():
    b = make()
    assert b.get_component_name() == "TerraPIN valley cross-section"
    assert "channel_bottom__elevation" in b.get_input_var_names()
    assert "valley__width" in b.get_output_var_names()
    assert b.get_grid_rank(0) == 0 and b.get_grid_size(0) == 1
    assert b.get_grid_type(0) == "scalar"
    assert b.get_var_units("valley__width") == "m"
    # initial state: bed one channel depth below the surface, width == channel width
    assert np.isclose(one(b, "channel_bottom__elevation"), -4.0)
    assert np.isclose(one(b, "valley__width"), 16.0)


def test_vertical_incise_exports_solid_sediment():
    b = make()
    b.set_value("channel_bottom__elevation", np.array([-15.0]))   # GRLP dz < 0
    b.update()
    assert np.isclose(one(b, "channel_bottom__elevation"), -15.0)
    solid = one(b, "channel_solid_sediment__volume")
    bulk = one(b, "channel_bulk_sediment__area")
    assert 0.0 < solid < bulk                                     # solid < bulk (porous alluvium)


def test_vertical_aggrade_is_a_sink():
    b = make()
    b.set_value("channel_bottom__elevation", np.array([-15.0])); b.update()
    b.set_value("channel_bottom__elevation", np.array([-9.0])); b.update()   # dz > 0
    assert one(b, "channel_solid_sediment__volume") < 0.0         # deposition removes from the river


def test_lateral_migrate_widens_the_valley():
    b = make()
    b.set_value("channel_bottom__elevation", np.array([-15.0])); b.update()
    w0 = one(b, "valley__width")
    b.set_value("channel__x_position", np.array([40.0])); b.update()          # the lateral driver
    assert np.isclose(one(b, "channel__x_position"), 40.0)
    assert one(b, "valley__width") > w0                          # strath is wider now


def test_time_advances_per_update():
    b = make()
    assert b.get_current_time() == 0.0
    b.set_value("channel_bottom__elevation", np.array([-12.0])); b.update()
    assert b.get_current_time() == b.get_time_step()
    b.update_until(3.0)
    assert b.get_current_time() >= 3.0


def test_get_set_value_roundtrip_and_finalize():
    b = make()
    b.set_value("channel__x_position", np.array([7.5]))
    assert np.isclose(one(b, "channel__x_position"), 7.5)
    b.finalize()
    assert b._model is None
