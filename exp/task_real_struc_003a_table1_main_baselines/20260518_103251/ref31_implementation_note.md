# ref31_implementation_note

`ref31` is the dense-reference physical baseline inside the reference-surface family. It uses the full 31-radius reference grid over 0.00-0.30 m with 0.01 m spacing. In the codebase this path is still invoked as `reconstruct_cylindrical_reference(method='BP')` because `PROTOCOL_V1.reference_sets['BP']` maps to the 31-radius grid. For Table 1, `T01_BP` is exact k-domain voxel-wise BP, while `T06_ref31` is this full-reference reference-surface approximation explicitly labeled as `ref31`.
