# Pcyc_encoding_audit

status: PASS

- Pcyc min/max/mean/std: -0.99930543 / 0.99999940 / 0.00107068 / 0.13635996
- sin(pi*Pcyc) min/max/mean/std: -1.00000000 / 1.00000000 / 0.00070108 / 0.16912279
- cos(pi*Pcyc) min/max/mean/std: -1.00000000 / 1.00000000 / 0.94394428 / 0.28348917
- corr(Pcyc, sin): 0.78225546
- corr(Pcyc, cos): -0.04528232
- ratio abs(Pcyc)<=0.25: 0.95790249
- ratio abs(Pcyc)>0.25: 0.04209751
- encoded-channel NaN count: 0
- encoded-channel Inf count: 0
- split channel shapes: {'train': [800, 1, 24, 24, 24], 'val': [100, 1, 24, 24, 24], 'test': [100, 1, 24, 24, 24]}
- max abs error of sin(pi*Pcyc)^2 + cos(pi*Pcyc)^2 - 1: 1.19209290e-07

The geometry tensors are generated from the same corrected x-y-z metadata grid as the ref3 volume. P01 excludes Pcyc from the learnable geometry branch but still uses scalar Pcyc to compute the fixed RSB envelope.
