import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import vsutil
import nnedi3_rpow2
import havsfunc as haf
import mvsfunc as mvf
import rvsfunc as INOX
core = vs.core
core.max_cache_size = 8192

from Mirumo_NCs import OP2, ED2
OP = OP2()
ED = ED2()
# THIS IS THE OP SOURCE
src = lvf.src(r"D:\Releases\Sources\Mirumo\Bonus Disc\Mirumo Bonus Disc_t04.mkv", force_lsmas=True)
src = src.std.SetFrameProp(prop="_Matrix", intval=6)
src = src.std.SetFrameProp(prop="_Transfer", intval=6)
src = src.std.SetFrameProp(prop="_Primaries", intval=6)
src = src.std.Limiter()

# Deinterlace and convert to 16 bit for working in high precision
deint = lvf.deinterlace.decomb(src, TFF=True, decimate=False)
# Decimate on EXTREMELY narrow thresholds. Artifacting is fairly consistent across frames here
decim = core.vivtc.VDecimate(deint, cycle=5, chroma=False, dupthresh=0.6, blockx=4, blocky=4)
decim = vsutil.depth(decim, 16)

resize = decim.resize.Spline36(height=540, width=decim.width)

# Crop off the black edges, it's bloat for modern playback
crop = core.std.Crop(resize, left=8, right=6, top=0, bottom=0) # 706 width remaining

# Darken the lines and mask, we'll need this to preserve detail
darken = haf.FastLineDarkenMOD(crop, strength=34, protection=4)
mask = core.std.Prewitt(darken).std.Maximum()
mask = vsutil.iterate(mask, core.std.Minimum, 2)

denoise = mvf.BM3D(crop, sigma=[1.7,1.2,1.2], radius1=3, profile1="fast", refine=1, full=False)
# Dering it for a cleaner view in some scenes with less aggressive denoising
dering = haf.HQDeringmod(denoise, mrad=2, mthr=42, nrmode=1, darkthr=3, sharp=0)
merged = core.std.MaskedMerge(dering, darken, mask)

# Use NNEDI3 to help fix aliasing on both chroma and luma
scaled = nnedi3_rpow2.nnedi3_rpow2(merged, correct_shift=True).resize.Spline36(width=706, height=540)
lines = core.std.MaskedMerge(scaled, merged, mask)

# Magic chromashift fixing bullshit, invented just for this!
shifted = INOX.chromashifter(lines)

deband = core.f3kdb.Deband(shifted, range=16, y=24, cb=18, cr=18, grainy=14, grainc=9, output_depth=16)

grain = kgf.adaptive_grain(deband, 0.2, luma_scaling=6.5)
out = vsutil.depth(grain, 10)

out.set_output(0)
crop.set_output(1)
