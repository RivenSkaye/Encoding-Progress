import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import vsutil
import mvsfunc as mvf
from placebo import deband as pdb
core = vs.core
core.max_cache_size = 10240
epnum = 4
epstring = f"0{epnum}" if epnum < 10 else str(epnum)
filenum = epnum+6
filestring = f"0{filenum}" if filenum < 10 else str(filenum)
src_file = f"D:/Releases/Sources/[BDMV][Anima Yell!][アニマエール!][Vol.1-Vol.4 Fin]/[BDMV][190213]アニマエール! Vol.4/BD/BDMV/STREAM/000{filestring}.m2ts"
src = lvf.src(src_file)
deep = vsutil.depth(src[24:-24], 16)

denoise_y = core.knlm.KNLMeansCL(deep, d=2, a=2, s=3, h=1.2, channels="Y")
denoise_c = core.knlm.KNLMeansCL(deep, d=1, a=2, s=2, h=0.8, channels="UV")
denoise_a = core.std.ShufflePlanes([denoise_y,denoise_c,denoise_c], [0,1,2], colorfamily=vs.YUV)
denoise_b = mvf.BM3D(deep, sigma=[2.1], ref=denoise_a, profile1="fast", radius1=3)
denoise = core.std.ShufflePlanes([denoise_b,denoise_a,denoise_a], [0,1,2], colorfamily=vs.YUV)

aa = lvf.aa.nneedi3_clamp(denoise, strength=1.1, mthr=0.30)

det_mask = lvf.mask.detail_mask(aa, rad=2, radc=1, brz_a=0.05, brz_b=0.09)
y,u,v = vsutil.split(aa)
deband_a = vsutil.join([pdb(y, threshold=2.0, grain=5.5), u, v])
deband = core.std.MaskedMerge(deband_a, aa, det_mask)

grain = kgf.adaptive_grain(deband, luma_scaling=5, strength=0.4)
out = vsutil.depth(grain, 10)
out.set_output()

if __name__ == '__vapoursynth__':
    from acsuite import eztrim
    eztrim(src_file, trims=(24,-24), ref_clip=src, outfile=f"D:/Releases/Cait-Sidhe/Anima Yell!/Ouen Doga/Anima_Yell!_Ouen_Doga-e{epstring}.mka")
