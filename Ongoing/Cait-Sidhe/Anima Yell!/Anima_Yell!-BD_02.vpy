import vapoursynth as vs
import rvsfunc as rvs
import lvsfunc as lvf
import kagefunc as kgf
import vsutil
import mvsfunc as mvf
import havsfunc as haf
from vardefunc import diff_creditless_mask as dcm
from placebo import deband as pdb
core = vs.core

from AY_NCs import OP, ED

# porting this to something that's a bit more flexible for ep3 onwards
def Scredit_mask(luma):
    luma = vsutil.depth(luma, 32)
    _descaled = core.descale.Debicubic(luma, vsutil.get_w(810), 810, b=0.2, c=0.4)
    _rescaled = core.resize.Bicubic(_descaled, 1920, 1080)
    _mask = core.std.Expr([vsutil.depth(luma, 32), _rescaled], 'x y - abs 0.060 < 0 1 ?')
    _mask = vsutil.iterate(_mask, core.std.Maximum, 6)
    _mask = vsutil.iterate(_mask, core.std.Inflate, 6)
    return _mask

NCOP = OP()[24:-24]
opstart = 2038
opend = 4197
NCED = ED()[24:-24]
edstart = 31794
edend = 33952

src = lvf.src(r"D:\Releases\Sources\[BDMV][Anima Yell!][アニマエール!][Vol.1-Vol.4 Fin]\[BDMV][181226]アニマエール! Vol.1\BD\BDMV\STREAM\00004.m2ts")
# Rescale using a modified version of Zastin's dogahomo()
rescale = rvs.questionable_rescale(vsutil.depth(src, 16), 810, b=0.2, c=0.4, mask_thresh=0.05)

# Detail- and linemasking for denoising
det_mask = lvf.mask.detail_mask(rescale, brz_a=0.25, brz_b=0.15)
denoise_ya = core.knlm.KNLMeansCL(rescale, d=2, a=3, s=4, h=1.2, channels="Y")
denoise_ca = core.knlm.KNLMeansCL(rescale, d=2, a=2, s=4, h=1.0, channels="UV")
denoise_a = core.std.ShufflePlanes([denoise_ya,denoise_ca,denoise_ca], [0,1,2], colorfamily=vs.YUV)
denoise_b = mvf.BM3D(rescale, sigma=[2.1], ref=denoise_a, profile1="fast", profile2="fast", refine=1, radius1=3)
# BM3D left some gunk in chroma, most noticeably around hard contrast edges
denoise = core.std.ShufflePlanes([denoise_b,denoise_a,denoise_a], [0,1,2], colorfamily=vs.YUV)
denoise = core.std.MaskedMerge(denoise, rescale, det_mask)
# Thanks for handling the effort of AA for me, Light
aa = lvf.aa.nneedi3_clamp(denoise, strength=0.75, mthr=0.30)
# Dehaloing it
dehalom = rvs.dehalo_mask(aa, iter_out=4)
dehalo_a = haf.DeHalo_alpha(aa, darkstr=0.8, brightstr=1.2)
dehalo_a = vsutil.depth(dehalo_a, 16)
dehalo = core.std.MaskedMerge(aa, dehalo_a, dehalom)
# Generate a new detail mask and deband it, putting back fine detail the way it was
det_mask = lvf.mask.detail_mask(dehalo, rad=2, radc=1, brz_a=0.05, brz_b=0.09)
y,u,v = vsutil.split(dehalo)
deband_a = vsutil.join([pdb(y, threshold=3.0, grain=6.5),
                        pdb(u, threshold=3.0, grain=2.0),
                        pdb(v, threshold=3.0, grain=2.0)])
deband = core.std.MaskedMerge(deband_a, dehalo, det_mask)

# Add grain
grain = kgf.adaptive_grain(deband, luma_scaling=7)
out = vsutil.depth(grain, 10)

# Merge credits onto the NCs and splice it in
scrad_op_mask = Scredit_mask(vsutil.get_y(src))[2038:4197]
scrad_ed_mask = Scredit_mask(vsutil.get_y(src))[31794:33952]
spliced = rvs.nc_splice(out, NCOP, opstart, opend, use_internal=True, ext_mask=vsutil.depth(scrad_op_mask, 10))
spliced = rvs.nc_splice(out, NCED, edstart, edend, use_internal=True, ext_mask=vsutil.depth(scrad_ed_mask, 10))

# Output and done
spliced[24:-24].set_output()
