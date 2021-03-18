import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import vsutil
import nnedi3_rpow2
import havsfunc as haf
import mvsfunc as mvf
core = vs.core

# Load the source, Part A of the ep. force LSMASH because this is a DVD remux
src = lvf.src(r"D:\Releases\Sources\Mirumo\Volume 10\fulldisc\ep37 - 2 - Part A.mkv", force_lsmas=True)

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
# 00000 - 00122: 0
# 00123 - 00553: 0.75
# 00554 - 00697: 0.125 => episode title? This text has bleed
# 00698 - 01219: 0.25
# 01220 - 01350: 0
# 01351 - 01439: 0.5
# 01440 - 01955: 0.25
# 01956 - 02913: 0.5
# 02914 - 03044: 0
# 03045 - 03196: 0.25
# 03170 - 03276: 0
# 03277 - 03487: 0.5
# 03488 - 03595: 0
# 03596 - 04199: 0.25
# 04200 - 04953: 0
# 04954 - 05012: 0.25
# 05013 - 08128: 0
# 08129 - 08322: 0.25
# 08323 - 13923: 0
# 13924 - 13982: 0.25
# 13983 - 14580: 0
# 14581 - 14645: 0.25
# 14646 - 14865: 0 END OF PART A

# Shift the U and V planes accordingly
res_u0 = core.resize.Spline16(u, height=resize_y.height/2, src_left=0)
res_u125 = core.resize.Spline16(u, height=resize_y.height/2, src_left=0.125)
res_u25 = core.resize.Spline16(u, height=resize_y.height/2, src_left=0.25)
res_u5 = core.resize.Spline16(u, height=resize_y.height/2, src_left=0.5)
res_u75 = core.resize.Spline16(u, height=resize_y.height/2, src_left=0.75)

res_v0 = core.resize.Spline16(v, height=resize_y.height/2, src_left=0)
res_v125 = core.resize.Spline16(v, height=resize_y.height/2, src_left=0.125)
res_v25 = core.resize.Spline16(v, height=resize_y.height/2, src_left=0.25)
res_v5 = core.resize.Spline16(v, height=resize_y.height/2, src_left=0.5)
res_v75 = core.resize.Spline16(v, height=resize_y.height/2, src_left=0.75)

resize_u = lvf.rfs(clip_a=res_u0, clip_b=res_u25, ranges=[(698, 1219), (1440, 1955), (3045, 3196), (3596, 4199), (4954, 5012), (8129, 8322), (13924, 13982), (14581, 14645)])
resize_u = lvf.rfs(clip_a=resize_u, clip_b=res_u125, ranges=[(554, 697)])
resize_u = lvf.rfs(clip_a=resize_u, clip_b=res_u5, ranges=[(1351, 1439), (1956, 2913), (3277, 3487)])
resize_u = lvf.rfs(clip_a=resize_u, clip_b=res_u75, ranges=[(123, 553)])

resize_v = lvf.rfs(clip_a=res_v0, clip_b=res_v25, ranges=[(698, 1219), (1440, 1955), (3045, 3196), (3596, 4199), (4954, 5012), (8129, 8322), (13924, 13982), (14581, 14645)])
resize_v = lvf.rfs(clip_a=resize_v, clip_b=res_v125, ranges=[(554, 697)])
resize_v = lvf.rfs(clip_a=resize_v, clip_b=res_v5, ranges=[(1351, 1439), (1956, 2913), (3277, 3487)])
resize_v = lvf.rfs(clip_a=resize_v, clip_b=res_v75, ranges=[(123, 553)])
# merge the clips to a full YUV vid again
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
dering = haf.HQDeringmod(denoise, mrad=2, mthr=42, nrmode=1, darkthr=3, sharp=0)
merged = core.std.MaskedMerge(dering, darken, mask)

# Use NNEDI3 to help fix aliasing on both chroma and luma
scaled = nnedi3_rpow2.nnedi3_rpow2(merged, correct_shift=False).resize.Spline36(width=706, height=540)

deband = core.f3kdb.Deband(scaled, range=16, y=24, cb=18, cr=18, grainy=14, grainc=9, output_depth=16)

grain = kgf.adaptive_grain(deband, 0.2, luma_scaling=6.5)
out = vsutil.depth(grain, 10)

out.set_output()
