import vapoursynth as vs
import lvsfunc as lvf
import fvsfunc as fvf
import havsfunc as haf
import kagefunc as kgf
from vsutil import *
core = vs.get_core()
core.max_cache_size = 8192

source_vid = lvf.src(r"D:/Releases/Tokimeki Memorial Ova/Volume 2/tokimeki memorial ova vol 2.d2v").std.CropRel(4, 4, 0, 0)
source_vid = haf.LUTDeCrawl(source_vid, ythresh=15, cthresh=10, maxdiff=50, scnchg=25, usemaxdiff=True, mask=False)
source_vid = core.std.AssumeFPS(source_vid, fpsnum=30000, fpsden=1001)
source_vid = lvf.decomb(source_vid, TFF=True, vinv=False)
source_vid = fvf.Depth(source_vid, 16)
episode = source_vid[1634:63169]
OP = episode[6284:9473]
OP = core.resize.Spline36(OP, 640, 480)
OP = kgf.adaptive_grain(OP, strength=0.25, static=True, luma_scaling=12, show_mask=False)
OP.set_output()