import vapoursynth as vs
import kagefunc as kgf
import lvsfunc as lvf
import havsfunc as haf
import fvsfunc as fvf
import vsTAAmbk as taa
from vsutil import get_w
core = vs.core

src = lvf.src(r'D:\Releases\Sources\Bakugan Shuuka\LPTD_1003E.Title3.d2v')
decombed = lvf.decomb(src, TFF=True, vinv=True, decimate=True)
# Grabbing just the ED from this thing
decombed = fvf.Depth(decombed[32249:33928], 32) # Waifu2x requires 32-bit
w2x = core.caffe.Waifu2x(decombed, noise=2, scale=1, model=6, cudnn=True)
# HQDeringmod requires it to be an integer format again
w2x = fvf.Depth(w2x, 16)
dering = haf.HQDeringmod(w2x, mrad=2, msmooth=3, incedge=True, nrmode=1, sharp=2, drrep=21)
# Somehow stretching sooner caused a boatload of artifacting
stretch = core.resize.Spline36(fvf.Depth(dering, 32), get_w(480), 480)
# Deband it, this was made worse with stretching but required either way
debanded = core.f3kdb.Deband(fvf.Depth(stretch, 16), y=56, cb=56, cr=56, grainy=0, output_depth=16)
# Make it pretty!
grain = kgf.adaptive_grain(debanded, 0.15, luma_scaling=20)
# Output 8-bit because it's going to be an AMQ webm
fvf.Depth(grain, 8).set_output()