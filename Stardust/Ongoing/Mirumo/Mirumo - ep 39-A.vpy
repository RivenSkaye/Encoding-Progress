import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import vsutil
import nnedi3_rpow2
import havsfunc as haf
import mvsfunc as mvf
core = vs.core

# Load the source, Part A of the ep. force LSMASH because this is a DVD remux
src = lvf.src(r"D:\Releases\Sources\Mirumo\Volume 10\fulldisc\ep39 - 2 - Part A.mkv", force_lsmas=True)

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
# 03045 - xxxxx: 0.25

# Shift the U plane values
res_u0 = core.resize.Spline16(u, width=706, height=540, src_left=0)
res_u125 = core.resize.Spline16(u, width=706, height=540, src_left=0.125)
res_u25 = core.resize.Spline16(u, width=706, height=540, src_left=0.25)
res_u5 = core.resize.Spline16(u, width=706, height=540, src_left=0.5)
res_u75 = core.resize.Spline16(u, width=706, height=540, src_left=0.75)

# Shift the V plane values
res_v0 = core.resize.Spline16(v, width=706, height=540, src_left=0)
res_v125 = core.resize.Spline16(v, width=706, height=540, src_left=0.125)
res_v25 = core.resize.Spline16(v, width=706, height=540, src_left=0.25)
res_v5 = core.resize.Spline16(v, width=706, height=540, src_left=0.5)
res_v75 = core.resize.Spline16(v, width=706, height=540, src_left=0.75)

resize = core.std.ShufflePlanes([resize_y, res_u25, res_v25], [0,0,0], vs.YUV)

resize.set_output()