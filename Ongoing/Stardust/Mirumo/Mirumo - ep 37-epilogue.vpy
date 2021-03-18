import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import vsutil
import nnedi3_rpow2
import havsfunc as haf
import mvsfunc as mvf
core = vs.core

# Load the source, Part A of the ep. force LSMASH because this is a DVD remux
src = lvf.src(r"D:\Releases\Sources\Mirumo\Volume 10\fulldisc\ep37 - 5 - epilogue.mkv", force_lsmas=True)

# Deinterlace and convert to 16 bit for working in high precision
deint = lvf.deinterlace.decomb(src, TFF=True, decimate=False)
# Decimate on EXTREMELY narrow thresholds. Artifacting is fairly consistent across frames here
decim = core.vivtc.VDecimate(deint, cycle=5, chroma=False, dupthresh=0.6, blockx=4, blocky=4)
decim = vsutil.depth(decim, 16)

# Split so we can fix the chroma shift
y,u,v = vsutil.split(decim)
# Resize to the correct aspect ratio. DVDs need stretching
resize_y = core.resize.Spline16(y, height=540)

# Resizing the chroma planes. And it looks like we'll be scenefiltering once again.
# There's varying chroma shifts again, range time:
# 00000 - 00898: 0
# 00899 - 01766: 0.25
# 01767 - 02368: 0
# 02369 - 02470: 0.25
# 02471 - 02553: 0
# 02554 - 02732: 0.25
# 02733 - 03541: 0
# 03542 - 03808: 0.25
# 03809 - 04811: 0
# 04812 - 05055: 0.25
# 05056 - 05403: 0
# 05404 - 05838: 0.25
# 05839 - 06659: 0
# 06660 - 06863: 0.25
# 06864 - 12243: 0
# 12244 - 12457: 0.25
# 12458 - 14231: 0
# 14232 - 14745: 0.25

# Shift the U and V planes accordingly
resize_u = core.resize.Spline16(u, height=resize_y.height/2, src_left=0.25)
resize_v = core.resize.Spline16(v, height=resize_y.height/2, src_left=0.25)
resize = core.std.ShufflePlanes([resize_y, resize_u, resize_v], [0,0,0], vs.YUV)

# Crop off the black edges, it's bloat for modern playback
crop = core.std.Crop(resize, left=8, right=6, top=0, bottom=0) # 706 width remaining

# edit the NCOP blanket to fit this
# Darken the lines and mask, we'll need this to preserve detail
darken = haf.FastLineDarkenMOD(crop, strength=34, protection=4)
mask = core.std.Prewitt(darken).std.Maximum()
mask = vsutil.iterate(mask, core.std.Minimum, 2)

# Replaced w2x with a good, but slow denoiser. Some scenes are still hurt, but it looks good
denoise = mvf.BM3D(darken, sigma=[1.7,1.2,1.2], radius1=3, profile1="fast", refine=1, full=False)
# Dering it for a cleaner view in some scenes with less aggressive denoising
dering = haf.HQDeringmod(denoise, mrad=2, mthr=32, nrmode=1, darkthr=3, sharp=0)
merged = core.std.MaskedMerge(dering, darken, mask)

# Use NNEDI3 to help fix aliasing on both chroma and luma
# Correct shift somehow messes up some of the earlier work. Not letting it correct seems to work well.
scaled = nnedi3_rpow2.nnedi3_rpow2(merged, correct_shift=False).resize.Spline36(width=706, height=540)

deband = core.f3kdb.Deband(scaled, range=16, y=24, cb=18, cr=18, grainy=14, grainc=6, output_depth=16)

grain = kgf.adaptive_grain(deband, 0.2, luma_scaling=6.5)
out = vsutil.depth(grain, 10)

out.set_output()
