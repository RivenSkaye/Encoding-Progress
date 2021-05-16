import vapoursynth as vs
from lvsfunc import src
core = vs.core
core.max_cache_size = 10240
from AY_NCs import OP as NCOP

NCOP(src(r"D:\Releases\Sources\[BDMV][Anima Yell!][アニマエール!][Vol.1-Vol.4 Fin]\[BDMV][181226]アニマエール! Vol.1\BD\BDMV\STREAM\00007.m2ts"))[24:-24].set_output()
