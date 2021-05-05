import vapoursynth as vs
import rvsfunc as rvs
import lvsfunc as lvf
import kagefunc as kgf
import vsutil
import mvsfunc as mvf
import havsfunc as haf
from placebo import deband as pdb
core = vs.core
def ED():
    src = lvf.src(r"D:\Releases\Sources\[BDMV][Anima Yell!][アニマエール!][Vol.1-Vol.4 Fin]\[BDMV][181226]アニマエール! Vol.1\BD\BDMV\STREAM\00008.m2ts")
    # Rescale using a modified version of Zastin's dogahomo()
    rescale = rvs.questionable_rescale(vsutil.depth(src, 16), 810, b=1/3, c=1/3, mask_thresh=0.05)

    # Detail- and linemasking for denoising
    det_mask = lvf.mask.detail_mask(rescale, brz_a=0.25, brz_b=0.15)
    denoise_ya = core.knlm.KNLMeansCL(rescale, d=2, a=3, s=3, h=1.2, channels="Y")
    denoise_ca = core.knlm.KNLMeansCL(rescale, d=2, a=2, s=3, h=1.0, channels="UV")
    denoise_a = core.std.ShufflePlanes([denoise_ya,denoise_ca,denoise_ca], [0,1,2], colorfamily=vs.YUV)
    denoise_b = mvf.BM3D(rescale, sigma=[1.9], ref=denoise_a, profile1="fast", radius1=3)
    # BM3D left some gunk in chroma, most noticeably around hard contrast edges
    denoise = core.std.ShufflePlanes([denoise_b,denoise_a,denoise_a], [0,1,2], colorfamily=vs.YUV)
    denoise = core.std.MaskedMerge(denoise, rescale, det_mask)
    # Thanks for handling the effort of AA for me, Light
    aa = lvf.aa.nneedi3_clamp(denoise, strength=1.25, mthr=0.25)
    # Dehaloing it
    dehalom = rvs.dehalo_mask(aa, iter_out=3)
    dehalo_a = haf.DeHalo_alpha(aa, darkstr=0.9, brightstr=1.1)
    dehalo_a = vsutil.depth(dehalo_a, 16)
    dehalo = core.std.MaskedMerge(aa, dehalo_a, dehalom)
    # Generate a new detail mask and deband it, putting back fine detail the way it was
    det_mask = lvf.mask.detail_mask(dehalo, rad=2, radc=1, brz_a=0.05, brz_b=0.09)
    y,u,v = vsutil.split(dehalo)
    deband_a = vsutil.join([pdb(y, threshold=3.0, grain=6.5),
                            pdb(u, threshold=3.0, grain=2.0),
                            pdb(v, threshold=3.0, grain=2.0)])
    deband = core.std.MaskedMerge(deband_a, dehalo, det_mask)

    # Finish up and output
    grain = kgf.adaptive_grain(deband, strength=0.65, luma_scaling=5)
    out = vsutil.depth(grain, 10)
    return out
