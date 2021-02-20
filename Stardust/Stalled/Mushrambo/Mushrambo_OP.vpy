import vapoursynth as vs
import lvsfunc as lvf
import vsutil
core = vs.core

src = lvf.src(r"D:\Releases\Sources\Mushrambo\Volume1\Mushrambo Volume 1 - chapter01.mkv", force_lsmas=True)
# These offsets change from time to time, which causes mad artifacting.
# To mitigate this, we'll be running the filters on all offsets and
# mixing results. Preferrably from normal cycle sets (5 interlaced -> 4 prog)
dkz0 = core.dotkill.DotKillZ(src, order=0, offset=0)
dkt0 = core.dotkill.DotKillT(dkz0, order=0, offset=0)
dkz1 = core.dotkill.DotKillZ(src, order=0, offset=1)
dkt1 = core.dotkill.DotKillT(dkz1, order=0, offset=1)
dkz2 = core.dotkill.DotKillZ(src, order=0, offset=2)
dkt2 = core.dotkill.DotKillT(dkz2, order=0, offset=2)
dkz3 = core.dotkill.DotKillZ(src, order=0, offset=3)
dkt3 = core.dotkill.DotKillT(dkz3, order=0, offset=3)
dkz4 = core.dotkill.DotKillZ(src, order=0, offset=4)
dkt4 = core.dotkill.DotKillT(dkz4, order=0, offset=4)

# Result sets:
# 0000 - 0203: 3
# 0204 - 0279: 0

deint = core.vivtc.VFM(dkt4, order=1, field=1, mode=3, mchroma=True, chroma=True, micmatch=2)
dks = core.dotkill.DotKillS(deint, iterations=4, usematch=False)
deint2 = lvf.deinterlace.decomb(dks, TFF=True, decimate=True, vinv=False)


deint2.set_output()