import vapoursynth as vs
import rvsfunc as rvs
import lvsfunc as lvf
import kagefunc as kgf
import vsutil
import mvsfunc as mvf
import havsfunc as haf
from placebo import deband as pdb
core = vs.core
core.max_cache_size = 10240
src = lvf.src(r"D:\Releases\Sources\[BDMV][Anima Yell!][アニマエール!][Vol.1-Vol.4 Fin]\[BDMV][190213]アニマエール! Vol.4\BD\BDMV\STREAM\00007.m2ts")
