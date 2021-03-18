import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import vsutil
import mvsfunc as mvf
import havsfunc as haf
import nnedi3_rpow2
core = vs.core
core.max_cache_size = 8192

src = lvf.src(r"D:\Releases\Sources\Mon Colle Knights movie\Demux\BCBA_0664.d2v")
# Default to TFF if not specified, use opposite field to restore.
# Use mode 5 and micmatch on every frame, gives the least bad results
deint = core.vivtc.VFM(src, order=1, field=3, mode=5, micmatch=2)
# Fix both leftover combing and some of the less painful frameblending.
# Makes frameblending overall less noticeable during playback.
# Mask is just a lower mthresh version of lvsfunc.deinterlace.decomb's that uses
# the first deinterlace pass rather than the source. Using source left more blends
combmask = core.comb.CombMask(deint, cthresh=1, mthresh=2)
combmask = core.std.Maximum(combmask, threshold=250).std.Maximum(threshold=250).std.Maximum(threshold=250).std.Maximum(threshold=250)
combmask = core.std.BoxBlur(combmask, hradius=2, vradius=2)
# Interpolate over any remaining combing in order to fix it
qtgmc = haf.QTGMC(deint, InputType=2, TFF=True, SourceMatch=3, Lossless=2, TR0=1, TR1=2, TR2=3, FPSDivisor=1)
# Merge according to the comb mask
qtgmc_merged = core.std.MaskedMerge(deint, qtgmc, combmask)
merged = vsutil.depth(qtgmc_merged, 16)

decim = core.vivtc.VDecimate(merged, chroma=True)
decim = decim[1178:]
# Split for fixing the chroma shift, yeet everything up to the menu
y,u,v = vsutil.split(decim)
res_y = core.resize.Spline36(y, height=540)
res_u = core.resize.Spline36(u, height=270, src_left=0.25)
res_v = core.resize.Spline36(v, height=270, src_left=0.25)
resize = vsutil.join([res_y, res_u, res_v])
# Chop off useless stuff shown before the menu and stretch
crop = core.std.CropRel(resize, left=6, right=4, top=6, bottom=0)

# Mask for some protection, darken the lines against scrubbing
darken = haf.FastLineDarkenMOD(crop, strength=26, protection=4)
mask = core.std.Prewitt(darken)
mask = core.std.Maximum(mask)
mask = vsutil.iterate(mask, core.std.Minimum, 2)

# Denoise the movie, it needs some help, but not too rough.
# Have BM3D and KNLM play nice together, seems to be a good solution
denoise_a = mvf.BM3D(darken, sigma=[1.4,1.0,1.0], radius1=3, profile1="fast", refine=1, full=False)
denoise_b = core.knlm.KNLMeansCL(darken, d=3, a=2, s=2, h=1.0, channels="Y", rclip=denoise_a)
denoise_c = core.knlm.KNLMeansCL(denoise_b, d=2, a=1, s=1, h=1.0, channels="UV", rclip=denoise_a)
denoise = core.std.MaskedMerge(denoise_c, darken, mask, planes=[0,1,2])

# Dehaloing and deringing in a slightly aggressive manner
# Also seems to catch some of the smaller blends
mask = core.std.Binarize(mask)
dehalo = haf.EdgeCleaner(denoise, strength=14, rmode=3, smode=1, hot=False)
dehalo = core.std.MaskedMerge(dehalo, denoise, mask)

# NNEDI3 to clean up some aliasing and lines. Hermite downscale to prevent oversharpening
nn = nnedi3_rpow2.nnedi3_rpow2(dehalo).resize.Bicubic(width=denoise.width, height=denoise.height, filter_param_a=1/3, filter_param_b=1/3)

# Running this after denoise severly lessens the green hue at the top in some scenes.
# For some reason the bottom edge of this thing is fine, but also the most blended
edged = core.edgefixer.ContinuityFixer(nn, left=4, right=3, top=3, bottom=0, radius=2)

# Debanding and grain before output
deband = core.f3kdb.Deband(edged, range=13, y=24, cb=16, cr=16, grainy=12, grainc=0, output_depth=16)
grain = kgf.adaptive_grain(deband, 0.4, luma_scaling=6)
out = vsutil.depth(grain, 10)
out.set_output()
