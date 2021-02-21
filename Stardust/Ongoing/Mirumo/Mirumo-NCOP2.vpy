import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import vsutil
import nnedi3_rpow2
import havsfunc as haf
import mvsfunc as mvf
core = vs.core

# Load the source, OP in this case. force LSMASH because this is a DVD remux
src = lvf.src(r"D:\Releases\Sources\Mirumo\Bonus Disc\Mirumo Bonus Disc_t04.mkv", force_lsmas=True)

# Deinterlace and convert to 16 bit for working in high precision
deint = lvf.deinterlace.decomb(src, TFF=True, decimate=False)
# Decimate on EXTREMELY narrow thresholds. Artifacting is fairly consistent across frames here
decim = core.vivtc.VDecimate(deint, cycle=5, chroma=False, dupthresh=0.4, blockx=4, blocky=4)
decim = vsutil.depth(decim, 16)

# Crop off the black edges, it's bloat for modern playback
crop = core.std.Crop(decim, left=8, right=6, top=0, bottom=0) # 706 width remaining

# Split so we can fix the chroma shift
y,u,v = vsutil.split(crop)
# Resize to the correct aspect ratio. DVDs need stretching
resize_y = core.resize.Spline16(y, height=540)

# The chroma shift is all over the place. Time to list ranges
# 0000-0287: 0.25
# 0288-0435: 0
# 0436-0537: 1.6
# 0538-0807: 0.25
# 0808-1432: 0
# 1433-1523: 1.1
# 1524-1555: 0.5
# 1556-1580: 1.1
# 1581-1631: 0.25
# 1632-1648: 0.5
# 1649-1667: 0
# 1668-1720: 0.5
# 1721-2158: 0
# Fix up the shift on the chroma planes and make this baby YUV444P16
res_u0 = core.resize.Spline16(u, width=706, height=540, src_left=0)
res_v0 = core.resize.Spline16(v, width=706, height=540, src_left=0)
res_u25 = core.resize.Spline16(u, width=706, height=540, src_left=0.25)
res_v25 = core.resize.Spline16(v, width=706, height=540, src_left=0.25)
res_u5 = core.resize.Spline16(u, width=706, height=540, src_left=0.5)
res_v5 = core.resize.Spline16(v, width=706, height=540, src_left=0.5)
res_u11 = core.resize.Spline16(u, width=706, height=540, src_left=1.1)
res_v11 = core.resize.Spline16(v, width=706, height=540, src_left=1.1)
res_u16 = core.resize.Spline16(u, width=706, height=540, src_left=1.6)
res_v16 = core.resize.Spline16(v, width=706, height=540, src_left=1.6)

# Mix and match the ranges for the U plane
resize_u = lvf.rfs(clip_a=res_u25, clip_b=res_u0, ranges=[(288, 435), (808, 1432), (1649, 1667), (1721, 2158)])
resize_u = lvf.rfs(clip_a=resize_u, clip_b=res_u16, ranges=[(436, 537)])
resize_u = lvf.rfs(clip_a=resize_u, clip_b=res_u11, ranges=[(1433, 1523), (1524, 1580)])
resize_u = lvf.rfs(clip_a=resize_u, clip_b=res_u5, ranges=[(1632, 1648), (1668, 1720)])

# Do the same for the V plane
resize_v = lvf.rfs(clip_a=res_v25, clip_b=res_v0, ranges=[(288, 435), (808, 1432), (1649, 1667), (1721, 2158)])
resize_v = lvf.rfs(clip_a=resize_v, clip_b=res_v16, ranges=[(436, 537)])
resize_v = lvf.rfs(clip_a=resize_v, clip_b=res_v11, ranges=[(1433, 1523), (1524, 1580)])
resize_v = lvf.rfs(clip_a=resize_v, clip_b=res_v5, ranges=[(1632, 1648), (1668, 1720)])

# Merge them again
resize = core.std.ShufflePlanes([resize_y, resize_u, resize_v], [0,0,0], vs.YUV)

# Darken the lines and mask, we'll need this to preserve detail
darken = haf.FastLineDarkenMOD(resize, strength=29, protection=9)
mask = core.std.Prewitt(darken)
mask = core.std.Maximum(mask)
mask = vsutil.iterate(mask, core.std.Minimum, 2)

# Replaced w2x with a good, but slow denoiser. Some scenes are still hurt, but it looks good
denoise = mvf.BM3D(darken, sigma=[3.6,2.2,2.2], radius1=3, profile1="fast", refine=1, full=False)
denoise = vsutil.depth(denoise, 16) # Convert back down to 16 for normal filters
merged = core.std.MaskedMerge(denoise, darken, mask)

# Use NNEDI3 to help fix aliasing on both chroma and luma
scaled = nnedi3_rpow2.nnedi3_rpow2(merged).resize.Spline36(width=706, height=540, format=vs.YUV420P16)

deband = core.f3kdb.Deband(scaled, range=16, y=24, cb=18, cr=18, grainy=14, grainc=9, output_depth=16)
grain = kgf.adaptive_grain(deband, 0.1, luma_scaling=8)
out = vsutil.depth(grain, 10)

out.set_output()
