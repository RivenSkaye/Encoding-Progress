import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import vsutil
import nnedi3_rpow2
import havsfunc as haf
import mvsfunc as mvf
import rvsfunc as INOX
from functools import partial
core = vs.core
core.max_cache_size = 8192

def NCOP2() -> vs.VideoNode:
    # Load the source, OP in this case. force LSMASH because this is a DVD remux
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
    masker = partial(core.std.Convolution, matrix=[-1] * 4 + [8] + [-1] * 4,
                 planes=[0, 1, 2], saturate=False)
    before = lines[:437]
    broken1 = lines[437:538]
    after = lines[538:1435]
    broken2 = lines[1435:1518]
    final = lines[1518:]
    shifted_a = INOX.dvd.chromashifter(before, maskfunc=masker)
    bry, bru, brv = vsutil.split(broken1)
    bru = bru.resize.Spline64(src_left=1.3)
    brv = brv.resize.Spline64(src_left=1.3)
    shifted_b = vsutil.join([bry,bru,brv])
    shifted_c = INOX.dvd.chromashifter(after, maskfunc=masker)
    bry, bru, brv = vsutil.split(broken2)
    bru = bru.resize.Spline64(src_left=1.5)
    brv = brv.resize.Spline64(src_left=1.5)
    shifted_d = vsutil.join([bry,bru,brv])
    shifted_e = INOX.dvd.chromashifter(final, maskfunc=masker)
    shifted = shifted_a+shifted_b+shifted_c+shifted_d+shifted_e

    deband = core.f3kdb.Deband(shifted, range=16, y=24, cb=18, cr=18, grainy=14, grainc=9, output_depth=16)

    # This scene has some special issues. So we're replacing a few frames.
    # No idea why this scene specifically had these issues
    # Until offending frame + replacement  + Remaining clip
    replace = deband[:1534] + deband[1535] + deband[1535:]
    replace = replace[:1538] + replace[1539] + replace[1539:]
    replace = replace[:1542] + replace[1543] + replace[1543:]
    replace = replace[:1550] + replace[1551] + replace[1551:]
    replace = replace[:1554] + replace[1555] + replace[1555:]
    replace = replace[:1570] + replace[1571] + replace[1571:]
    replace = replace[:1573] + replace[1572] + replace[1574:]
    replace = replace[:1577] + replace[1576] + replace[1578:]

    grain = kgf.adaptive_grain(deband, 0.2, luma_scaling=6.5)
    out = vsutil.depth(grain, 10)

    return out
