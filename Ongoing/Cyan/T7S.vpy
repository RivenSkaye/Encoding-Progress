import lvsfunc as lvf
import rvsfunc as rvf
from debandshit import placebo_deband as pdb
import kagefunc as kgf
import vsutil
import vapoursynth as vs
core = vs.core

src_file = r"D:\Releases\Sources\T7S\TOKYO_7TH_SISTERS\BDMV\STREAM\00002.m2ts"

# Load in the source and filter in 16-bit precision
# Native 1080p which is friggin orgasmic since no descale effort
src = lvf.src(src_file)
src = vsutil.depth(src, 16, sample_type=vs.INTEGER)

# We're scenefiltering, these are special ranges
ranges = {
    # No filter for pure black frames, we're replacing those with a blank clip
    # since that'll save a lot of resources getting wasted on source frames!
    "pure_black": (
                   (3927,3976), (4000,4024), (10158,10179), (10957,10976),
                   (12126,12146), (12988,13009), (14573,14586), (17062,17079),
                   (23023,23047), (47429,47447), (49055,49067), (65164,65176),
                   (75944, 75956), (95238,95322), (105646,105673), (109512,109608)
                  ),
    # Scenes shot on the phone cam have intentional chromatic abbaration and
    # generally look worse, more flat in color and just pain. We'll give 'em
    # some light filtering, but we want the contrast with the rest of the film
    # to be visible as a nice, personal touch
    "phonecam": (
                 (3976,4575), (4680,4777), (4920,4968), (5501,5657), (7215,7402),
                 (7527,7569), (7830,7916), (8103,8358), (8665,8750), (9333,9448),
                 (9645,9753), (9948,10158), (10471,10637), (10901,10957),
                 (11456,11601), (11798,12125), (12188,12312), (12473,12482),
                 (13435,13512), (13601,13806), (15162,15239), (15359,15426),
                 (103855,104023)
                ),
    # Namecards are a royal pain in the ass thanks to lines and fine detail
    "namecards": (
                  (4777,4920), (7402,7527), (8750,8880), (9448,9645), (10310,10429),
                  (11601,11684), (12312,12473), (13512,13601), (15239,15359),
                  (16288,16343)
                 ),
    # Encoder memes are happening here
    "SD_JPG": (14586,14748),
    # These scenes need to be protected even more thanks to them being very
    # sensitive and may fuck up at any time...
    "protecc": (
                (976,1332), (21416,22832), (25687,25831), (37635,37730),
                (37892,37969), (38124,38496), (46904,47429), (48610,48941),
                (67916,69903), (70010,75944), (95321,98237), (98382,98955),
                (99208,100726)
               ),
    "OP": (1332,3927),
    "ED": (105646,109751),
    "dear_jesus": (
                   (37470,37635), (37730,37892), (37969,38017), (38865,38985),
                   (47447,47591), (48941,49055), (76118,76154), (76586,76622),
                   (77517,77609), (78184,78316), (78475,80402), (80802,81027),
                   (84853,84877), (85117,85352), (91308,91380), (92042,92097),
                   (98237,98382), (98955,99208), (100773,100995)
                  )
}


def denoise(clip: vs.VideoNode) -> vs.VideoNode:
    denoise_ya = core.knlm.KNLMeansCL(clip, d=3, a=4, s=3, h=1.2, channels="Y")
    denoise_ca = core.knlm.KNLMeansCL(clip, d=3, a=3, s=3, h=1.1, channels="UV")
    return core.std.ShufflePlanes([denoise_ya, denoise_ca, denoise_ca], planes=[0,1,2], colorfamily=vs.YUV)


def deband(clip: vs.VideoNode) -> vs.VideoNode:
    y, u, v = vsutil.split(clip)
    return vsutil.join([pdb(y, radius=12.5, threshold=3.0, grain=6.5),
                        pdb(u, radius=8.75, threshold=3.0, grain=1.5),
                        pdb(v, radius=8.75, threshold=3.0, grain=1.5)])


def softdenoise(clip: vs.VideoNode) -> vs.VideoNode:
    """
    Your everyday masked denoise for less damage than usual!
    """
    det_mask = lvf.mask.detail_mask(clip, rad=3, radc=2, brz_a=0.065, brz_b=0.037)
    den = denoise(clip)
    return core.std.MaskedMerge(den, clip, det_mask)


def protected_denoise(clip: vs.VideoNode) -> vs.VideoNode:
    """
    The merger of two masks to protect every little detail possible.

    This is for the live scenes and other high-detail bits.
    """
    flm = rvf.masking.fineline_mask(clip, thresh=3214)
    flm = flm.std.Maximum().std.Maximum().std.Maximum().std.Minimum().std.Minimum().std.Minimum()
    flm = vsutil.depth(flm, 16)
    ldm = lvf.mask.detail_mask(clip, rad=3, radc=2, brz_a=0.055, brz_b=0.037)
    ldm = vsutil.depth(ldm, 16)
    msk = core.std.Expr([flm, ldm], "x y < y x ?")
    den = denoise(clip)
    return core.std.MaskedMerge(den, clip, msk)

def protected_deband(clip: vs.VideoNode) -> vs.VideoNode:
    flm = rvf.masking.fineline_mask(clip, thresh=3214)
    flm = flm.std.Maximum().std.Maximum().std.Maximum().std.Minimum().std.Minimum().std.Minimum()
    flm = vsutil.depth(flm, 16)
    ldm = lvf.mask.detail_mask(clip, rad=3, radc=2, brz_a=0.065, brz_b=0.037)
    ldm = vsutil.depth(ldm, 16)
    msk = core.std.Expr([flm, ldm], "x y < y x ?")
    y, u, v = vsutil.split(clip)
    deb = vsutil.join([pdb(y, radius=14.5, threshold=3.6, grain=8.3),
                       pdb(u, radius=9.25, threshold=2.2, grain=1.0),
                       pdb(v, radius=9.25, threshold=2.4, grain=1.0)])
    grain = kgf.adaptive_grain(clip)
    return core.std.MaskedMerge(deb, grain, msk)

def camfilter(clip: vs.VideoNode) -> vs.VideoNode:
    """
    Minimal filtering for the cam scenes. Going a bit stronger on the chroma
    denoising and tossing dynamic grain on there.
    """
    den = denoise(clip)
    deb = deband(den)
    deb = vsutil.depth(deb, 10)
    return kgf.adaptive_grain(deb, strength=0.45, luma_scaling=8, static=False)

def dfj(clip: vs.VideoNode) -> vs.VideoNode:
    denoise_ya = core.knlm.KNLMeansCL(clip, d=3, a=1, s=2, h=0.6, channels="Y")
    denoise_ca = core.knlm.KNLMeansCL(clip, d=3, a=1, s=2, h=0.45, channels="UV")
    den = core.std.ShufflePlanes([denoise_ya, denoise_ca, denoise_ca], planes=[0,1,2], colorfamily=vs.YUV)
    flm = rvf.masking.fineline_mask(clip, thresh=2052)
    ldm = lvf.mask.detail_mask(clip, rad=2, radc=1, brz_a=0.045, brz_b=0.022)
    msk = vsutil.depth(core.std.Expr([flm, ldm], "x y < y x ?"), 16)
    merge = core.std.MaskedMerge(den, clip, msk)
    deb = protected_deband(merge)
    grnmsk = kgf.adaptive_grain(deb, strength=0.8, static=True,
                                luma_scaling=8, show_mask=True)
    return vsutil.depth(core.std.MaskedMerge(deb, merge, grnmsk), 10)

def ed_fix(clip: vs.VideoNode) -> vs.VideoNode:
    luma = vsutil.get_y(clip)
    mask = luma.std.Binarize(threshold=25600).std.Maximum()
    blank = core.std.BlankClip(clip, length=clip.num_frames)
    fixed = core.std.MaskedMerge(blank, clip, mask)
    return vsutil.depth(fixed, 10)


# Special filtering for these scenes
camd = camfilter(src)
ED = ed_fix(src)
pain = dfj(src)

# Denoise
pr_den = protected_denoise(src)
norm_den = softdenoise(src)
den = rvf.utils.replace_ranges(norm_den, pr_den, ranges.get("protecc"))

# Dehalo
dehal = lvf.dehalo.bidehalo(den, sigmaS=1.1, sigmaR=5/510,
                            sigmaS_final=0.3, sigmaR_final=2/510)
dehal = rvf.utils.replace_ranges(dehal, den, ranges.get("protecc"))
dehal = rvf.utils.replace_ranges(dehal, den, ranges.get("OP"))
dehal = rvf.utils.replace_ranges(dehal, den, ranges.get("namecards"))

# Deband
pr_deb = protected_deband(dehal)
norm_deb = deband(dehal)
deb = rvf.utils.replace_ranges(norm_deb, pr_deb, ranges.get("protecc"))
deb = rvf.utils.replace_ranges(deb, pr_deb, ranges.get("namecards"))
deb = rvf.utils.replace_ranges(deb, pr_deb, ranges.get("OP"))

# GRAIIIINNNNN
deb = vsutil.depth(deb, 10)
grain = kgf.adaptive_grain(deb, strength=0.33, static=True, luma_scaling=9)
grain = rvf.utils.replace_ranges(grain, camd, ranges.get("phonecam"))
grain = rvf.utils.replace_ranges(grain, camd, ranges.get("SD_JPG"))
black = core.std.BlankClip(grain, length=grain.num_frames)
out = rvf.utils.replace_ranges(grain, black, ranges.get("pure_black"))
out = rvf.utils.replace_ranges(out, ED, ranges.get("ED"))
out = rvf.utils.replace_ranges(out, pain, ranges.get("dear_jesus"))
out = out[24:-24]

# out.set_output(0)

# Splitting up the encode, this thing is MASSIVE
fragment = 1
frag_size = 13713  # We're encoding the movie in 8 sections
fs = (fragment - 1) * frag_size
fe = fs + frag_size
chunk = out[fs:fe]


if __name__ == "__vapoursynth__" and fe == out.num_frames:
    from acsuite import eztrim
    eztrim(src_file, trims=(24,-24), ref_clip=src, outfile=r"D:\Releases\Cyan\T7S\T7S.mka")

