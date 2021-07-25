import vapoursynth as vs
from lvsfunc import src
core = vs.core
core.max_cache_size = 10240
from AY_NCs import OP as NCOP

src_file = r"D:\Releases\Sources\[BDMV][Anima Yell!][アニマエール!][Vol.1-Vol.4 Fin]\[BDMV][181226]アニマエール! Vol.1\BD\BDMV\STREAM\00007.m2ts"
out = NCOP(src(src_file))[24:-24]
out.set_output()

if __name__ == '__vapoursynth__':
    from acsuite import eztrim
    eztrim(src_file, trims=(24,-24), ref_clip=out, outfile=r"D:\Releases\Cait-Sidhe\Anima Yell!\Anima_Yell-NCOP.mka")
