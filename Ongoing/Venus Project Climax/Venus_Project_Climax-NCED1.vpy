import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
from nnedi3_rpow2 import nnedi3_rpow2 as npow2
import vapoursynth as vs
core = vs.core

#Load in the source
source_vid = lvf.src(r"D:\Releases\Sources\[BDMV] Venus Project Climax\VenusProject Climax Vol 4\BDMV\STREAM\00008.m2ts")
# Clip back to legal range. Thanks for pointing it out Light-senpai!
# Wrote a glorious memefunc that actually helped me figure stuff out
y, u, v = kgf.split(source_vid)
# scales it back from out-of-bounds values to legal values for the limited range
y = core.std.Expr(y, "x 16 max 235 min")
descale = fvf.Depth(kgf.inverse_scale(y, 1280, 720, "bicubic", b=0, c=1), 16)
rescaled = npow2(descale).resize.Spline36(1920, 1080)
joined = kgf.join([rescaled, fvf.Depth(u, 16), fvf.Depth(v, 16)])
deband = core.f3kdb.Deband(joined, grainy=12, grainc=16, sample_mode=1, blur_first=False, dynamic_grain=False, output_depth=16)
grain = kgf.adaptive_grain(deband, strength=0.4, luma_scaling=9.5)
out = fvf.Depth(grain, 10)
out.set_output()