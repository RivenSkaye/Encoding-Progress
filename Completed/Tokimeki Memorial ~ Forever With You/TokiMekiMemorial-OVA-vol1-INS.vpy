import vapoursynth as vs
import lvsfunc as lvf
import fvsfunc as fvf
import havsfunc as haf
import kagefunc as kgf
from vsutil import *
core = vs.get_core()
core.max_cache_size = 8192

source_vid = lvf.src(r"D:/Releases/Tokimeki Memorial Ova/Volume 1/tokimeki memorial ova vol 1.d2v").std.CropRel(4, 4, 0, 0)
source_vid = haf.LUTDeCrawl(source_vid, ythresh=15, cthresh=10, maxdiff=50, scnchg=25, usemaxdiff=True, mask=False)
source_vid = core.std.AssumeFPS(source_vid, fpsnum=30000, fpsden=1001)
source_vid = lvf.decomb(source_vid, TFF=True, vinv=False)
source_vid = fvf.Depth(source_vid, 16)
episode = source_vid[3303:61511]
INS = episode[38210:42795]
INS = core.resize.Spline36(INS, 640, 480)
INS = kgf.adaptive_grain(INS, strength=0.25, static=True, luma_scaling=12, show_mask=False)
INS.set_output()