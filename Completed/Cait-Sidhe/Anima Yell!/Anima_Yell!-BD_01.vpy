import vapoursynth as vs
import rvsfunc as rvs
import lvsfunc as lvf
import kagefunc as kgf
import vsutil
import mvsfunc as mvf
import havsfunc as haf
from debandshit import placebo_deband as pdb
core = vs.core
core.max_cache_size = 10240
# This show uses the OP as ED for ep 1
from AY_NCs import OP as NCED
ed_src = lvf.src(r"D:\Releases\Sources\[BDMV][Anima Yell!][アニマエール!][Vol.1-Vol.4 Fin]\[BDMV][181226]アニマエール! Vol.1\BD\BDMV\STREAM\00007.m2ts")
# Do the filtering and set it aside for now
src_file = r"D:\Releases\Sources\[BDMV][Anima Yell!][アニマエール!][Vol.1-Vol.4 Fin]\[BDMV][181226]アニマエール! Vol.1\BD\BDMV\STREAM\00003.m2ts"
src = lvf.src(src_file)
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

# Finish up and output
grain = kgf.adaptive_grain(deband, luma_scaling=7)
out = vsutil.depth(grain, 10)
# Use the NCOP to do a better job of cleaning up the OP as ED
scrad_ed_mask = rvs.Scradit_mask(src, b=0.2, c=0.4, height=810, iters=6, absthresh=0.055)[31552:33709]
scrad_ed_mask = core.morpho.Close(vsutil.depth(scrad_ed_mask, 10), size=9).std.Binarize()
nced = NCED(ed_src)[24:-24]
spliced = rvs.nc_splice(out, nced, 31552, 33709, use_internal=True, ext_mask=scrad_ed_mask)
spliced = spliced[24:-24]
spliced.set_output()

if __name__ == '__vapoursynth__':
    from acsuite import eztrim
    eztrim(src_file, trims=(24,-24), ref_clip=src, outfile=r"D:\Releases\Cait-Sidhe\Anima Yell!\Anima_Yell-e01.mka")
