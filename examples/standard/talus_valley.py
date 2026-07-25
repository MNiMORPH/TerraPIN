#! /usr/bin/env python
"""
Fluvial then hillslope: a channel abandons a wall, which then sheds talus.

A channel incises and migrates away to the right, leaving the LEFT valley wall
abandoned above a fresh strath (fluvial work, `sweep`). With the river gone, that
wall does hillslope work: `retreat('left', dx)` steps the exposed face back and
piles the shed rock as talus (colluvium) at its base, the apron growing and
burying the wall as the retreat decelerates. This is the river-absent counterpart
to the channel's erosion -- the interplay a MIGRATING channel unlocks.

Uses only the public API (`StandardTerrapin.retreat`); the talus is placed by the
same repose machinery the symmetric model uses, in the bounded wall-strath corner.

Run in the dedicated environment:
    conda run -n terrapin python examples/standard/talus_valley.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from shapely.geometry import box

from terrapin.standard import StandardTerrapin

REPOSE = {"bedrock": 75.0, "alluvium": 32.0, "colluvium": 20.0}

st = StandardTerrapin()
st.set_bodies({"bedrock":  box(-120.0, -70.0, 120.0, -8.0),
               "alluvium": box(-120.0,  -8.0, 120.0,  0.0)})
st.set_repose_angles(REPOSE)
st.set_channel_position(0.0)
st.set_channel_elevation(0.0)
st.set_channel_width(16.0)
st.set_channel_depth(4.0)
st.establish_channel()
st.incise(-20.0)         # cut a deep valley (a tall left wall to shed from)
st.migrate(55.0)         # migrate right -> the LEFT wall is abandoned above its strath

fig, axes = plt.subplots(2, 3, figsize=(13.0, 6.6), sharex=True, sharey=True)
ax = axes.ravel()
st.plot(ax=ax[0], show_terraces=False)
ax[0].set_title("fluvial: incise + migrate right\n(left wall abandoned)", fontsize=9.5, fontweight="bold")
for k in range(1, 6):
    st.retreat("left", 3.0)
    st.plot(ax=ax[k], show_terraces=False)
    ax[k].set_title("hillslope: retreat %d" % k, fontsize=9.5, fontweight="bold")

VE = 3.0
for a in ax:
    a.set_xlim(-90.0, 90.0); a.set_ylim(-26.0, 4.0); a.set_aspect(VE)

handles = [Patch(facecolor=c, edgecolor="k", hatch=h, label=k)
           for k, (c, h) in StandardTerrapin._STYLE.items()]
handles.append(Patch(facecolor="#2b7bba", edgecolor="k", label="river"))
fig.legend(handles=handles, loc="lower center", ncol=6, fontsize=8.5,
           frameon=False, bbox_to_anchor=(0.5, 0.0))
fig.suptitle("A river abandons a wall; the wall sheds talus (fluvial then hillslope, "
             "vertical exaggeration %g×)" % VE, fontsize=13, fontweight="bold")
fig.subplots_adjust(left=0.05, right=0.98, top=0.88, bottom=0.12, hspace=0.5, wspace=0.22)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "talus_valley.png")
fig.savefig(out, dpi=140, bbox_inches="tight")
print("wrote", out)
