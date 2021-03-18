import vapoursynth as vs
import lvsfunc as lvf
import fvsfunc as fvf
import havsfunc as haf
import kagefunc as kgf
core = vs.core

src = lvf.src(r"D:\Downloads\AMQ\[Burger] Shiawasette Naani.mkv")
src = fvf.Depth(src, 16)
src = core.vivtc.VDecimate(src)
crop = core.std.Crop(src, 2, 2, 0, 0)
edge = core.edgefixer.ContinuityFixer(crop, [2,2,2], [2,2,2], [2,2,2], [2,2,2])
deblock = core.deblock.Deblock(edge, 35, 3)
dering = haf.HQDeringmod(haf.EdgeCleaner(deblock, rmode=21, hot=True), mrad=2, mthr=70, nrmode=2)
deband = fvf.Depth(core.f3kdb.Deband(dering, grainy=9, grainc=12, sample_mode=1, blur_first=False, dynamic_grain=False), 32)
w2x = core.caffe.Waifu2x(deband, 0, 4, 16, 12, 4)
dehalo = fvf.Depth(haf.FineDehalo(w2x, rx=0.8, ry=0.6, darkstr=0.8, brightstr=0.8), 16)
down = core.dpid.Dpid(dehalo, 310, 238)
out = kgf.adaptive_grain(down, strength=0.35, luma_scaling=9.5)
out.set_output()