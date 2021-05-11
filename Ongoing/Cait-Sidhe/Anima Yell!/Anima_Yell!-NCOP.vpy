import vapoursynth as vs
core = vs.core
core.max_cache_size = 1024*10
from AY_NCs import OP as NCOP

NCOP()[24:-24].set_output()
