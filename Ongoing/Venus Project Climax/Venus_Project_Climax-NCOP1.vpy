import lvsfunc as lvf
import fvsfunc as fvf
import mvsfunc as mvf
import havsfunc as haf
import kagefunc as kgf
import vapoursynth as vs
import xaa
from nnedi3_rpow2 import nnedi3_rpow2 as npow2
import vsTAAmbk as taa
core = vs.core

source_vid = lvf.src(r"D:\Releases\Sources\[BDMV] Venus Project Climax\VenusProject Climax Vol 4\BDMV\STREAM\00007.m2ts")
source_vid = core.std.Expr(source_vid, "x 16 max 240 min")
source_vid = kgf.inverse_scale(source_vid, width=1280, height=720)
deep = fvf.Depth(source_vid, 16)
denoise = mvf.BM3D(deep, sigma=[1.0,0.8], depth=16, profile1="lc")
REE_SCENE = denoise[89:419]
sharpening_range1 = denoise[484:541]
sharpening_range2 = denoise[627:659]
sharpening_range3 = denoise[694:737]
shthese = [sharpening_range1, sharpening_range2, sharpening_range3]
sharpened = []
for sh in shthese:
	sharpened.append(core.msmoosh.MSharpen(sh, threshold=0.9, strength=45, mask=False))
blocks = []
for aa in sharpened:
	blocks.append(xaa.xaa(aa, mode="dr b SangNom", mtype="Sobel", csharp=1, mask=1, cstr=2.4, mthr=7, chroma=1, eedimthr=0.3))
# Splice them all together for further filtering
processed = denoise[0:89]+REE_SCENE+denoise[419:484]+blocks[0]+denoise[541:627]+blocks[1]+denoise[659:694]+blocks[2]+denoise[737:]
clean = haf.EdgeCleaner(processed, smode=1, rep=True, strength=4.5)
dehalo = haf.FineDehalo(clean)
rescaled = npow2(dehalo).resize.Spline36(1920, 1080)
grain = kgf.adaptive_grain(rescaled, strength=0.20, luma_scaling=6)
out = fvf.Depth(grain, 10)
out.set_output()