import vapoursynth as vs
import lvsfunc as lvf
import fvsfunc as fvf
import havsfunc as haf
import kagefunc as kgf
core = vs.get_core()
core.max_cache_size = 8192
# Get the source
source_vid = lvf.src(r"D:/Releases/Sources/Voltron/VOLTRON_COLLECTION_1___DISC_3___.d2v")
source_vid = lvf.decomb(source_vid, TFF=True, decimate=False, vinv=False)
source_vid = core.std.CropRel(source_vid, left=16, right=10, top=2, bottom=2)
# Chop out the INS Elodie needs
INS = source_vid[130607:136596]
INS = core.resize.Point(INS, format=vs.YUV420P8, range=1, range_in=0)
INS = fvf.Depth(INS, 32, range_in='full')
#Filtering
# Sorry Light, but blowing this up with waifu2x caused the filters to actually work
INS = core.caffe.Waifu2x(INS, 0, 4, 128, 120, 2)
# Thanks Kage, not letting this die again. And not taking chances on waifu2x
INS = fvf.Depth(INS, 16)
INS = kgf.adaptive_grain(INS, 0.5, luma_scaling=6)
# Better kick it back down because 32 float is unsupported
INS = core.edgefixer.ContinuityFixer(INS, [16, 16, 16], [16, 16, 16], [16, 16, 16], [16, 16, 16])
# This saved my ass so much! Dehaloed enough to improve, didn't kill intended haloing
INS = haf.FineDehalo(INS)
# Now we scale back down and clip it within all legal ranges
INS = kgf.inverse_scale(INS, 640, 480)
INS = fvf.Depth(INS, 16)
# Output and encode or play
INS.set_output()