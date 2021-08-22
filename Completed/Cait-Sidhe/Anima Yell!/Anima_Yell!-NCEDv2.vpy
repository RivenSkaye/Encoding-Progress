import vapoursynth as vs
from lvsfunc import src
core = vs.core
core.max_cache_size = 10240
from AY_NCs import ED as NCED

src_file = r"D:\Releases\Sources\[BDMV][Anima Yell!][アニマエール!][Vol.1-Vol.4 Fin]\[BDMV][190213]アニマエール! Vol.3\BD\BDMV\STREAM\00008.m2ts"
sauce = src(src_file)
out = NCED(sauce)[24:-24]
out.set_output()

if __name__ == '__vapoursynth__':
    from acsuite import eztrim
    eztrim(src_file, trims=(24,-24), ref_clip=sauce, outfile=r"D:\Releases\Cait-Sidhe\Anima Yell!\Anima_Yell-NCEDv2.mka")
