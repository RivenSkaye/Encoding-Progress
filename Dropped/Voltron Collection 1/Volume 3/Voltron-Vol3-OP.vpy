import vapoursynth as vs
import lvsfunc as lvf
import fvsfunc as fvf
import havsfunc as haf
import kagefunc as kgf
core = vs.get_core()
core.max_cache_size = 8192
# Get the source
source_vid = lvf.src(r"D:/Releases/Sources/Voltron/VOLTRON_COLLECTION_1___DISC_3___.d2v")
source_vid = lvf.decomb(source_vid, TFF=True, decimate=False, vinv=True)
source_vid = core.std.CropRel(source_vid, left=16, right=10, top=2, bottom=2)
# Chop out the OP as this is creditless everywhere
OP = source_vid[3400:5280]
OP = fvf.Depth(OP, 32)
OP = core.resize.Spline36(OP, 640, 480)
#Filtering
# Sorry Light, but blowing this up with waifu2x caused the filters to actually work
OP = core.caffe.Waifu2x(OP, 0, 4, 128, 120, 2)
# Thanks Kage, not letting this die again. And not taking chances on waifu2x
OP = core.std.Limiter(OP, 0.0, 1.0)
OP = kgf.adaptive_grain(OP, 0.5, luma_scaling=6)
# Better kick it back down because 32 float is unsupported
OP = fvf.Depth(OP, 16)
OP = core.edgefixer.ContinuityFixer(OP, [16, 16, 16], [16, 16, 16], [16, 16, 16], [16, 16, 16])
# This saved my ass so much! Dehaloed enough to improve, didn't kill intended haloing
OP = haf.FineDehalo(OP)
# Now we scale back down and clip it within all legal ranges
OP = kgf.inverse_scale(OP, 640, 480)
OP = fvf.Depth(OP, 16)
# Output and encode or play
OP.set_output()