import vapoursynth as vs
import rvsfunc as rvs
import stgfunc as stg
import dfttest2 as dftt
import havsfunc as haf
import kagefunc as kgf
import vsutil
import vsaa
import vskernels

core = vs.core

sauce = (
    r"D:\Martin\[BDMV][210818] ARIA "
    r"The CREPUSCOLO\SHBR_0636\BDMV\STREAM\00002.m2ts"
)
src = vsutil.depth(core.lsmas.LWLibavSource(sauce).std.Limiter(), 16)
src_pre = src
black = core.std.BlankClip(src, length=24, keep=True)
unfiltered = black + src[24:714]
src = src[714:]


den_a = dftt.DFTTest(src, ftype=1, sigma=6.0, sigma2=5.0, backend=dftt.Backend.CPU())
den = core.std.ShufflePlanes([den_a, src, src], planes=[0, 1, 2], colorfamily=vs.YUV)

dark = haf.FastLineDarkenMOD(den, strength=18, thinning=1)
aa_a = vsaa.upscaled_sraa(dark, 1.4, downscaler=vskernels.Robidoux())
linemask = rvs.masking.fineline_mask(den, 69).std.Maximum().std.Minimum()
aa_a = den.std.MaskedMerge(aa_a, linemask, 0)
aa_b = vsaa.based_aa(den, rfactor=2.2)
aa = vsaa.clamp_aa(den, aa_a, aa_b, planes=0)

deb = stg.auto_deband(aa[:85567], 10, 1.4, steps=5)

final_mask = kgf.adaptive_grain(deb, strength=0.45, luma_scaling=9, show_mask=True)
final = core.std.MaskedMerge(deb, src, final_mask, 0)

end = aa[85567:]
black = core.std.BlankClip(end, keep=True)
recred_mask = end.std.Binarize(55 << 8).std.Maximum()
recred = core.std.MaskedMerge(black, end, recred_mask)


out = vsutil.depth(unfiltered + final + recred, 10)
out.set_output()
