import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import vsutil
import nnedi3_rpow2
import havsfunc as haf
import mvsfunc as mvf
import awsmfunc as awf
core = vs.core
core.max_cache_size = 8192

def NCED2() -> vs.VideoNode:
    # Load the source, OP in this case. force LSMASH because this is a DVD remux
    src = lvf.src(r"D:\Releases\Sources\Mirumo\Bonus Disc\Mirumo Bonus Disc_t05.mkv", force_lsmas=True)

    # Deinterlace and convert to 16 bit for working in high precision
    deint = lvf.deinterlace.decomb(src, TFF=True, decimate=False)
    # Decimate on EXTREMELY narrow thresholds. Artifacting is fairly consistent across frames here
    decim = core.vivtc.VDecimate(deint, cycle=5, chroma=False, dupthresh=0.4, blockx=4, blocky=4)
    decim = vsutil.depth(decim, 16)

    # Split so we can fix the chroma shift
    y,u,v = vsutil.split(decim)
    # Resize to the correct aspect ratio. DVDs need stretching
    resize_y = core.resize.Spline16(y, height=540)

    # Fix up the shift on the chroma planes
    resize_u = core.resize.Spline16(u, height=resize_y.height/2, src_left=0.25)
    resize_v = core.resize.Spline16(v, height=resize_y.height/2, src_left=0.25)

    # Merge them again
    resize = core.std.ShufflePlanes([resize_y, resize_u, resize_v], [0,0,0], vs.YUV)

    # Crop off the black edges, it's bloat for modern playback
    crop = core.std.Crop(resize, left=8, right=6, top=0, bottom=0) # 706 width remaining

    # Darken the lines and mask, we'll need this to preserve detail
    darken = haf.FastLineDarkenMOD(crop, strength=34, protection=4)
    mask = core.std.Prewitt(darken).std.Maximum()
    mask = vsutil.iterate(mask, core.std.Minimum, 2)

    # Replaced w2x with a good, but slow denoiser. Some scenes are still hurt, but it looks good
    denoise = mvf.BM3D(darken, sigma=[1.2,0.7,0.7], radius1=3, profile1="fast", refine=1, full=False)
    # Dering it for a cleaner view in some scenes with less aggressive denoising
    dering = haf.HQDeringmod(denoise, mrad=2, mthr=48, nrmode=1, darkthr=3, sharp=0)
    merged = core.std.MaskedMerge(dering, darken, mask)

    # Use NNEDI3 to help fix aliasing on both chroma and luma
    scaled = nnedi3_rpow2.nnedi3_rpow2(merged, correct_shift=False).resize.Spline36(width=706, height=540)

    edge = core.edgefixer.ContinuityFixer(scaled, left=2, top=0, right=3, bottom=0, radius=4)

    deband = core.f3kdb.Deband(edge, range=16, y=24, cb=18, cr=18, grainy=14, grainc=3, output_depth=16)

    grain = kgf.adaptive_grain(deband, 0.1, luma_scaling=8)
    out = vsutil.depth(grain, 10)
    return out
