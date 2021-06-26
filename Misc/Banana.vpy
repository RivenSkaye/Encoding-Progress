import vapoursynth as vs
import kagefunc as kgf
import lvsfunc as lvf
import rvsfunc as rvs
import havsfunc as haf
import vsutil
import nnedi3_rpow2
core = vs.core

# Load in the source
src_file = r"F:\Banana\episode.mkv"
src = lvf.src(src_file, force_lsmas=True)
# Deinterlace and decimate it
deint = src.tivtc.TFM(order=1, PP=6).tivtc.TDecimate(mode=1)[16536:17759]

# Fix the edges being broken, edgefixer doesn't do all planes by default.
# And if it does, it's broken because it turned cyan into pink
y,u,v = vsutil.split(deint)
edgy = y.edgefixer.ContinuityFixer(left=5, right=3, top=0, bottom=0, radius=8)
edgu = u.edgefixer.ContinuityFixer(left=3, right=2, top=0, bottom=0, radius=4)
edgv = v.edgefixer.ContinuityFixer(left=3, right=2, top=0, bottom=0, radius=4)
edge = vsutil.join([edgy,edgu,edgv])

# Filtering bitdepth time
edge = vsutil.depth(edge, 16)

# Perform AA, the use of NNEDI3+EEDI3 helps with leftover combing too
# Immediately stretch the thing to anamorphic output as well.
aa_a = lvf.aa.upscaled_sraa(edge, 1.3, width=720, height=540)
aa_b = lvf.aa.upscaled_sraa(aa_a.std.Transpose(), 1.8, width=540, height=720)
aa = aa_b.std.Transpose()

# Denoise it
denoise_y = aa.knlm.KNLMeansCL(d=1, a=2, s=3, h=1.4, channels="Y")
denoise_c = aa.knlm.KNLMeansCL(d=1, a=2, s=3, h=1.1, channels="UV")
denoise = core.std.ShufflePlanes([denoise_y,denoise_c,denoise_c], [0,1,2], colorfamily=vs.YUV)

# Dehalo the thing, it needs it
dehalom = rvs.dehalo_mask(aa)
dehalo_a = haf.DeHalo_alpha(aa, darkstr=0.7, brightstr=1.4)
dehalo_a = vsutil.depth(dehalo_a, 16)
dehalo = core.std.MaskedMerge(aa, dehalo_a, dehalom)

# deband, grain, output
det_mask = lvf.mask.detail_mask(dehalo, rad=2, radc=1, brz_a=0.05, brz_b=0.09)
deband_a = core.f3kdb.Deband(dehalo, range=16, y=24, cb=16, cr=16, grainy=14, grainc=3, output_depth=16)
deband = core.std.MaskedMerge(deband_a, dehalo, det_mask)

out = kgf.adaptive_grain(deband, strength=0.5, luma_scaling=8)
out = vsutil.depth(out, 8)
out.set_output()

if __name__ == '__vapoursynth__':
    from acsuite import eztrim
    eztrim(src_file, trims=(20670,22200), outfile=r"D:\banana.mka")
