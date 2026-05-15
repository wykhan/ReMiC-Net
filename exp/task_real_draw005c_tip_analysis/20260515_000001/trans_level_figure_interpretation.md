# Trans-level figure interpretation

## Figure caption candidate

Dense-volume Y-shaped target reconstructed with reduced-reference cylindrical operators and residual learning. Columns show the ground truth, ref3, ref9, BP, the positive residual predicted by the calibrated U-Net, and the final ref3+U-Net reconstruction. Rows show a Manisali-style translucent 3D volume rendering followed by dB maximum-intensity projections in the x-y, z-y, and x-z planes. The added x-z view exposes the axial separation of the forked tips and reveals structured losses that can be hidden when only x-y and z-y projections are inspected.

## Main-text interpretation

The four-row layout is designed to separate volumetric continuity from projection-dependent visibility. The 3D row verifies whether each method preserves a connected Y-shaped support, while the x-y, z-y, and x-z dB projections test the same object under complementary collapses of depth. The x-z projection is especially useful for this target because the two upper branches and the lower stem differ in both lateral position and height; a missing terminal response can therefore be distinguished from a mere overlap artifact in the x-y or z-y views.

The reduced-reference results exhibit a structured mismatch rather than random blur. In ref3, the left upper tip lies 0.0245 m from its nearest reference radius, whereas the right upper and lower tips lie 0.0711 m and 0.0600 m away, respectively. This radial placement helps explain why one upper terminal remains more visible while the other upper terminal and the lower terminal are suppressed or spread below the display threshold. Ref9 reduces the radial mismatch for the left and right upper tips to 0.0155 m and 0.0089 m, which is consistent with the recovery of both upper tips. The lower tip remains less clearly expressed even under ref9 because the denser reference set does not eliminate residual model mismatch, and the local response is more susceptible to projection and threshold suppression along the stem direction.

The ref3+U-Net column is more interpretable than a residual-only display because it shows the final physical reconstruction after compensation, while the residual panel isolates where the learned correction adds support to the reduced-reference output. This pairing makes the figure useful for explaining both the failure mode of coarse reference operators and the mechanism by which a learned residual can repair connected volumetric structure.

## Brief discussion note for the manuscript

The figure should be used as a main qualitative example with a short supporting note on tip-to-reference-surface distances. It demonstrates that the error pattern is geometry dependent: increasing the number of reference radii improves the forked upper branches, but does not fully remove the lower-stem failure. This is a stronger claim than a generic improvement statement because it links visual recovery to the target's radial placement with respect to the operator design.

## Optional Chinese explanation note for internal use

这张图建议作为正文主图或正文主图加补充说明使用。x-z 视图补上后，Y 形结构三个端点在高度和横向上的关系更清楚；ref3/ref9 的差异也能用端点到参考半径面的距离来解释，而不是只做主观视觉判断。ref3+U-Net 应作为最终重建结果展示，残差列只用于解释学习补偿的位置。

## Local diagnostic note

The local peak/support table below is a diagnostic aid rather than a standalone metric.

| Tip | Method | local peak r=2 | support >=0.10 | retained >=22% method peak |
| --- | --- | ---: | ---: | --- |
| left upper tip | GT | 0.5528 | 18 | True |
| left upper tip | ref3 | 0.5842 | 59 | True |
| left upper tip | ref9 | 0.0926 | 0 | False |
| left upper tip | BP | 0.5051 | 23 | True |
| left upper tip | U-Net residual | 0.1766 | 4 | False |
| left upper tip | ref3+U-Net | 0.5490 | 20 | True |
| right upper tip | GT | 0.4920 | 10 | True |
| right upper tip | ref3 | 0.0506 | 0 | False |
| right upper tip | ref9 | 0.1884 | 7 | True |
| right upper tip | BP | 0.2956 | 9 | True |
| right upper tip | U-Net residual | 0.4658 | 11 | True |
| right upper tip | ref3+U-Net | 0.4818 | 12 | True |
| lower tip | GT | 0.6023 | 32 | True |
| lower tip | ref3 | 0.1363 | 41 | True |
| lower tip | ref9 | 0.2710 | 21 | True |
| lower tip | BP | 0.5475 | 63 | True |
| lower tip | U-Net residual | 0.5149 | 29 | True |
| lower tip | ref3+U-Net | 0.5933 | 35 | True |
