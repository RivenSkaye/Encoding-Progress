import lvsfunc as lvf
import fvsfunc as fvf
import kagefunc as kgf
import havsfunc as haf
import vapoursynth as vs
core = vs.core
# Load in the source, clamp it because this DVD is cursed as hell
src = lvf.src(r"D:\Releases\Sources\Mon Colle Knights movie\BCBA_0664.d2v")
src = core.std.Limiter(src)
# Grab just the ED for AMQ and decomb it. TFF=True gives mad blending independent of frame
# TFF=False is much less bad but still leaves a lot of room for improvement
decomb = lvf.decomb(src[49251:58190], TFF=False, vinv=True, decimate=True)
decomb = fvf.Depth(decomb, 16)
cropped = core.std.CropRel(decomb[1:], left=6, right=4, top=0, bottom=0)
resized = core.resize.Spline36(cropped, width=640, height=480)
# This has shifted chroma, the DVD is cursed and gross. How did I like this as a kid?
y,u,v = kgf.split(resized)
u = core.resize.Spline16(u, u.width, u.height, src_left=0.25)
v = core.resize.Spline16(v, v.width, v.height, src_left=0.25)
deshifted = kgf.join([y,u,v])
edged = core.edgefixer.ContinuityFixer(deshifted, [4,2,2], [4,2,2], [4,2,2], [4,2,2], 2)
# This thing needs a lot of help
# Start out with some softer denoising, helps prevent the mask catching some of the blending too
denoised = kgf.hybriddenoise(edged)
# Edgemask because they get hit a bit too hard in this. But the mask picks up a bit too much
edgemask = kgf.retinex_edgemask(denoised, 1.5).std.Deflate().std.Deflate().std.Deflate()
# Use w2x to denoise much stronger, fix a lot of compression issues
w2x = core.caffe.Waifu2x(fvf.Depth(denoised, 32), noise=2, scale=1, block_w=16, block_h=12, model=2, cudnn=True)
dering = haf.HQDeringmod(fvf.Depth(w2x, 16), incedge=True, nrmode=1, sharp=2)
# Now merge them to restore a lot of the damage and keep the good parts
merged = core.std.MaskedMerge(dering, edged, edgemask)
dehalo = haf.FineDehalo(merged, rx=2.1, ry=1.6, darkstr=0.6, brightstr=0.8)
deband = core.f3kdb.Deband(dehalo, 6, y=15, cb=10, cr=10, grainy=8, grainc=0, output_depth=16)
grain = kgf.adaptive_grain(deband, 0.6, luma_scaling=14)
fvf.Depth(grain, 8).set_output()