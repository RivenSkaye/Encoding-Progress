import lvsfunc as lvf
import kagefunc as kgf
import fvsfunc as fvf
import havsfunc as haf
import vapoursynth as vs
core = vs.core

src = lvf.src(r"D:\Releases\Sources\Patlabor-WXIII_and_Minipato.d2v")
minipato = src[156159:]
decomb = lvf.decomb(minipato, TFF=True, decimate=False, vinv=True, rep=2)
# If this works, I'm starting my own *func
def PAL_deblend():
    return None
out = decomb
out.set_output()