import vapoursynth as vs
import kagefunc as kgf
import lvsfunc as lvf

src = lvf.src(r"F:\Banana\episode.mkv", force_lsmas=True)
deint = src.tivtc.TFM(order=1, PP=6)
deint.set_output()
