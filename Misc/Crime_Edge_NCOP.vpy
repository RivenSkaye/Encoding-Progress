import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import mvsfunc as mvf
import havsfunc as haf
from nnedi3_rpow2 import nnedi3_rpow2 as npow2
import vapoursynth as vs
import vsutil
core = vs.core

source_vid = lvf.src(r"D:\AMQ\Crime Edge\NCOP.m2ts")
y,u,v = vsutil.split(source_vid)
y = core.std.Limiter(y, 16, 230)
descale = fvf.Depth(kgf.inverse_scale(y, 1280, 720, "bicubic", b=0, c=1), 16)
denoise = mvf.BM3D(descale, sigma=[1.4,0], depth=16, profile1='lc')
deband = core.f3kdb.Deband(denoise, range=18, grainy=12, grainc=16, sample_mode=2, blur_first=False, dynamic_grain=False, output_depth=16)
rescaled = vsutil.join([npow2(deband).resize.Spline36(1920, 1080),fvf.Depth(u,16),fvf.Depth(v,16)])
out = kgf.adaptive_grain(rescaled, strength=0.35, luma_scaling=8.5)
fvf.Depth(out, 10).set_output()