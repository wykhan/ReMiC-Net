# failure_taxonomy

This file summarizes ET failure modes using review-style heuristic tagging on the reconstructed amplitude volumes.

## Labels

- `F1`: overall blur / global smearing
- `F2`: edge break / contour fracture
- `F3`: thin-structure disappearance
- `F4`: support fragmentation
- `F5`: local geometric shift
- `F6`: weak-return region suppression

## Counts By Method

- `ref3`: F1=49, F2=64, F3=25, F4=25, F5=36, F6=21
- `ref5`: F1=8, F2=86, F3=31, F4=13, F5=36, F6=27
- `ref7`: F1=6, F2=85, F3=35, F4=11, F5=32, F6=32
- `ref9`: F1=3, F2=90, F3=28, F4=12, F5=20, F6=22
- `BP`: F1=2, F2=56, F3=9, F4=16, F5=7, F6=9

## Counts By Family And Method

### L-shape

- `ref3`: F1=8, F2=11, F3=6, F4=3, F5=7, F6=4
- `ref5`: F1=1, F2=19, F3=12, F4=1, F5=10, F6=7
- `ref7`: F1=0, F2=21, F3=12, F4=5, F5=5, F6=7
- `ref9`: F1=0, F2=21, F3=11, F4=4, F5=3, F6=5
- `BP`: F1=0, F2=16, F3=2, F4=4, F5=2, F6=1

### cross

- `ref3`: F1=5, F2=15, F3=3, F4=5, F5=5, F6=1
- `ref5`: F1=0, F2=17, F3=4, F4=5, F5=6, F6=2
- `ref7`: F1=1, F2=17, F3=3, F4=2, F5=2, F6=2
- `ref9`: F1=0, F2=18, F3=2, F4=3, F5=2, F6=1
- `BP`: F1=0, F2=12, F3=0, F4=4, F5=1, F6=0

### double-line

- `ref3`: F1=5, F2=13, F3=3, F4=3, F5=7, F6=3
- `ref5`: F1=1, F2=14, F3=3, F4=2, F5=2, F6=2
- `ref7`: F1=0, F2=14, F3=3, F4=0, F5=5, F6=4
- `ref9`: F1=0, F2=15, F3=3, F4=1, F5=3, F6=5
- `BP`: F1=0, F2=6, F3=1, F4=4, F5=0, F6=0

### line

- `ref3`: F1=7, F2=10, F3=2, F4=3, F5=5, F6=4
- `ref5`: F1=2, F2=15, F3=5, F4=2, F5=9, F6=6
- `ref7`: F1=1, F2=13, F3=5, F4=2, F5=7, F6=6
- `ref9`: F1=2, F2=15, F3=4, F4=0, F5=6, F6=3
- `BP`: F1=1, F2=9, F3=3, F4=2, F5=3, F6=3

### point_cluster

- `ref3`: F1=19, F2=0, F3=0, F4=0, F5=3, F6=2
- `ref5`: F1=4, F2=0, F3=0, F4=0, F5=3, F6=5
- `ref7`: F1=4, F2=0, F3=0, F4=0, F5=5, F6=7
- `ref9`: F1=1, F2=0, F3=0, F4=0, F5=2, F6=3
- `BP`: F1=1, F2=0, F3=0, F4=0, F5=0, F6=3

### small_rect_edge

- `ref3`: F1=5, F2=15, F3=11, F4=11, F5=9, F6=7
- `ref5`: F1=0, F2=21, F3=7, F4=3, F5=6, F6=5
- `ref7`: F1=0, F2=20, F3=12, F4=2, F5=8, F6=6
- `ref9`: F1=0, F2=21, F3=8, F4=4, F5=4, F6=5
- `BP`: F1=0, F2=13, F3=3, F4=2, F5=1, F6=2
