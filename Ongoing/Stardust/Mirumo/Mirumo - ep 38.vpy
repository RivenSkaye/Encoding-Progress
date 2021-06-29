import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import vsutil
import nnedi3_rpow2
import havsfunc as haf
import mvsfunc as mvf
core = vs.core
core.max_cache_size = 8192

from Mirumo_NCs import NCOP2, NCED2
OP = NCOP2()
ED = NCED2()
src_a = lvf.src(r"D:\Releases\Sources\Mirumo\Volume 10\fulldisc\ep38 - 2 - Part A.mkv", force_lsmas=True)
src_b = lvf.src(r"D:\Releases\Sources\Mirumo\Volume 10\fulldisc\ep38 - 3 - Part B.mkv", force_lsmas=True)
src_epilogue = lvf.src(r"D:\Releases\Sources\Mirumo\Volume 10\fulldisc\ep38 - 5 - epilogue.mkv", force_lsmas=True)

def preshift(src):
    # Deinterlace and convert to 16 bit for working in high precision
    deint_a = lvf.deinterlace.decomb(src_a, TFF=True, decimate=False)
    # Decimate on EXTREMELY narrow thresholds. Artifacting is fairly consistent across frames here
    decim = core.vivtc.VDecimate(deint, cycle=5, chroma=False, dupthresh=0.6, blockx=4, blocky=4)
    decim = vsutil.depth(decim, 16)

    # Split so we can fix the chroma shift
    y,u,v = vsutil.split(decim)
    # Resize to the correct aspect ratio. DVDs need stretching
    resize_y = core.resize.Spline16(y, height=540)
    return resize_y, u, v

res_ya, ua, va = preshift(src_a)
res_yb, ub, vb = preshift(src_b)
res_yc, uc, vc = preshift(src_epilogue)

# Insert magic chromashift fixing bullshit here

# merge the clips to a full YUV vid again
resize_a = core.std.ShufflePlanes([res_ya, res_ua, res_va], [0,0,0], vs.YUV)
resize_b = core.std.ShufflePlanes([res_yb, res_ub, res_vb], [0,0,0], vs.YUV)
resize_c = core.std.ShufflePlanes([res_yc, res_uc, res_vc], [0,0,0], vs.YUV)

def postshift(resize) -> vs.VideoNode:
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

post_a = postshift(resize_a)
post_b = postshift(resize_b)
post_c = postshift(resize_c)
out = OP+post_a+post_b+ED+post_c
out.set_output()
