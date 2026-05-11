# task_real_008_report

## Task Goal

Build and evaluate ReMiC-Net with RSB-FiLM on the frozen 800/100/100 datasets and compare it against a residual 3D U-Net baseline under the same ref3 backbone.

## Frozen Baseline Reused

- Prior frozen baseline reference root: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717`
- Prior checkpoint audited: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717/checkpoints/frozen_mainline/best.pt`
- Direct reuse for the main comparison: no
- Reason: task_real_008 freezes residual-only output, while the prior 006d checkpoint was trained as direct image prediction. Baseline-U-Net was retrained here under the residual protocol for a controlled comparison.

## Protocol / Context Files Used

- `CONTEXT/real_cylindrical_master_document_rsb_film_updated20260510.md`
- `CONTEXT/model_structure_rsb_film_updated20260510.md`
- `CONTEXT/reference_surface_strategy_rsb_film_updated20260510.md`
- `CONTEXT/simulation_protocol_rsb_film_updated20260510.md`
- `CONTEXT/visualization_protocol.md`
- `PROMPTS/system_rules.md`
- `PROMPTS/review_checklist.md`

## Boundary Statement

- Data protocol: frozen 800/100/100 main split plus existing OOD sets only
- Physics backbone: `ref3` only
- Comparison scope: `Baseline-U-Net` vs `ReMiC-Net with RSB-FiLM` only
- `delta_rho_input = raw_meter`
- No support head, no generic FiLM main result, no physics-consistency, no new datasets

## ReMiC-Net Construction

- Main input: `X_ref3`
- Geometry branch input: `[Mshell, delta_rho_raw, Pcyc]`
- `Mshell`: 3-channel one-hot shell allocation map for ref3 radii `[0.00, 0.15, 0.30] m`
- `delta_rho_raw`: signed radial deviation in meter, used directly as the network input
- `Pcyc`: wrapped two-way phase deviation normalized by `pi`
- RSB-FiLM defaults: `epsilon_m=0.05`, `alpha_gamma=0.5`, `alpha_beta=0.1`
- Engineering note: the repository baseline trunk has a two-downsample 3D U-Net. RSB-FiLM was therefore applied to all available encoder, bottleneck, and decoder stages in that shallower trunk as the closest faithful implementation of the frozen placement rule.

## Input Metadata Construction

- Metadata source manifest: `exp/task_real_006d_800_formal/20260419_112717/learning_handoff_manifest_main_800_100_100.json`
- `fc = 34500000000.0 Hz`
- `lambda_c = 0.008695652174 m`
- `k_c^(2w) = 1445.132568 rad/m`
- Cached metadata manifest: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_008_remicnet_eval/20260511_082329/remicnet_input_manifest_008.json`

## Training Setup

- Dataset source: frozen main split from `006d`
- Epochs: 5
- Batch size: 4
- Optimizer: Adam
- Learning rate: 0.001
- Loss: residual L1
- Checkpoints:
  - baseline: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_008_remicnet_eval/20260511_082329/checkpoints/baseline/best.pt`
  - remicnet: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_008_remicnet_eval/20260511_082329/checkpoints/remicnet/best.pt`

## Main Test Comparison

[
  {
    "dataset": "Main Test",
    "method": "Baseline-U-Net",
    "NMSE_mean": 1.0002546301811395,
    "PSNR_mean": 30.158862104713503,
    "SSIM_mean": 0.4941027712190263,
    "runtime_mean": 0.38211554143473675,
    "speedup_vs_BP": 5.166031292907792,
    "num_samples": 100
  },
  {
    "dataset": "Main Test",
    "method": "ReMiC-Net",
    "NMSE_mean": 0.9986431509032545,
    "PSNR_mean": 30.168659101512375,
    "SSIM_mean": 0.49791392905255194,
    "runtime_mean": 0.382579436784722,
    "speedup_vs_BP": 5.1597672398400185,
    "num_samples": 100
  }
]

## OOD Comparison

{
  "Unseen-Parameter OOD": [
    {
      "dataset": "Unseen-Parameter OOD",
      "method": "Baseline-U-Net",
      "NMSE_mean": 0.9780945769277153,
      "PSNR_mean": 27.09095340443282,
      "SSIM_mean": 0.3283020241911921,
      "runtime_mean": 0.5650105115000043,
      "speedup_vs_BP": 5.772100375828831,
      "num_samples": 100
    },
    {
      "dataset": "Unseen-Parameter OOD",
      "method": "ReMiC-Net",
      "NMSE_mean": 0.96929915196645,
      "PSNR_mean": 27.130095628426467,
      "SSIM_mean": 0.3353451777174927,
      "runtime_mean": 0.5660350404399924,
      "speedup_vs_BP": 5.761652817891505,
      "num_samples": 100
    }
  ],
  "Leave-One-Family-Out Focused OOD": [
    {
      "dataset": "Leave-One-Family-Out Focused OOD",
      "method": "Baseline-U-Net",
      "NMSE_mean": 1.0174783631864124,
      "PSNR_mean": 31.41709694156296,
      "SSIM_mean": 0.5629134932765609,
      "runtime_mean": 0.3790007395699422,
      "speedup_vs_BP": 4.711097765422603,
      "num_samples": 100
    },
    {
      "dataset": "Leave-One-Family-Out Focused OOD",
      "method": "ReMiC-Net",
      "NMSE_mean": 1.0333975934252673,
      "PSNR_mean": 31.351391744085323,
      "SSIM_mean": 0.5599386751182819,
      "runtime_mean": 0.3800280336699734,
      "speedup_vs_BP": 4.69836269719,
      "num_samples": 100
    }
  ],
  "Random-ET OOD": [
    {
      "dataset": "Random-ET OOD",
      "method": "Baseline-U-Net",
      "NMSE_mean": 1.094637620481279,
      "PSNR_mean": 28.913163272074108,
      "SSIM_mean": 0.39105909347502704,
      "runtime_mean": 1.6937276681100046,
      "speedup_vs_BP": 3.9146446084320217,
      "num_samples": 100
    },
    {
      "dataset": "Random-ET OOD",
      "method": "ReMiC-Net",
      "NMSE_mean": 1.1578222151536786,
      "PSNR_mean": 28.70740519023358,
      "SSIM_mean": 0.3679816511710711,
      "runtime_mean": 1.6947592642599967,
      "speedup_vs_BP": 3.912261773069025,
      "num_samples": 100
    }
  ]
}

## Mismatch-Aware Diagnostic Results

- grouped by `|delta_rho|` uses support-mean `abs(delta_rho_raw)` per sample
- grouped by `|Pcyc|` uses support-mean `abs(Pcyc)` per sample
- `|Pcyc| <= 0.25` vs `> 0.25` uses support-mean phase-deviation grouping
- grouped delta rows: [{"bucket": "[0.000, 0.010)", "num_samples": "37", "baseline_nmse_mean": "1.0165694080855154", "remicnet_nmse_mean": "1.0428760430978254", "baseline_psnr_mean": "29.42451646499705", "remicnet_psnr_mean": "29.358125803780823", "baseline_ssim_mean": "0.44846583789619504", "remicnet_ssim_mean": "0.4464432732230012"}, {"bucket": "[0.010, 0.025)", "num_samples": "116", "baseline_nmse_mean": "1.0184724655414212", "remicnet_nmse_mean": "1.034093436623472", "baseline_psnr_mean": "29.176308752642786", "remicnet_psnr_mean": "29.121620750589578", "baseline_ssim_mean": "0.43258604580950843", "remicnet_ssim_mean": "0.4294382969403663"}, {"bucket": "[0.025, 0.040)", "num_samples": "108", "baseline_nmse_mean": "1.0122799793039579", "remicnet_nmse_mean": "1.0241776235403701", "baseline_psnr_mean": "28.46890579552227", "remicnet_psnr_mean": "28.428801121310304", "baseline_ssim_mean": "0.39419018667627603", "remicnet_ssim_mean": "0.3914269662424008"}, {"bucket": "[0.040, 0.055)", "num_samples": "77", "baseline_nmse_mean": "1.0385997789371648", "remicnet_nmse_mean": "1.0697618780155003", "baseline_psnr_mean": "30.100993144695934", "remicnet_psnr_mean": "30.00614073831646", "baseline_ssim_mean": "0.47910990779944546", "remicnet_ssim_mean": "0.46967545312687675"}, {"bucket": "[0.055, 0.076]", "num_samples": "62", "baseline_nmse_mean": "1.0321326489144604", "remicnet_nmse_mean": "1.038582434715632", "baseline_psnr_mean": "30.523070156595054", "remicnet_psnr_mean": "30.493760430090532", "baseline_ssim_mean": "0.5064599651374729", "remicnet_ssim_mean": "0.505573830752539"}]
- grouped pcyc rows: [{"bucket": "[0.000, 0.100)", "num_samples": "8", "baseline_nmse_mean": "1.0798306661019517", "remicnet_nmse_mean": "1.1856621507770826", "baseline_psnr_mean": "28.823490041446917", "remicnet_psnr_mean": "28.57172076559756", "baseline_ssim_mean": "0.394489595755343", "remicnet_ssim_mean": "0.3814728776776086"}, {"bucket": "[0.100, 0.250)", "num_samples": "63", "baseline_nmse_mean": "0.985361944247852", "remicnet_nmse_mean": "0.9850119096681633", "baseline_psnr_mean": "27.814594933250127", "remicnet_psnr_mean": "27.82135074650493", "baseline_ssim_mean": "0.3651524987577458", "remicnet_ssim_mean": "0.36818293331244833"}, {"bucket": "[0.250, 0.500)", "num_samples": "251", "baseline_nmse_mean": "1.0289372789304772", "remicnet_nmse_mean": "1.0489144683731813", "baseline_psnr_mean": "29.5148634768187", "remicnet_psnr_mean": "29.44857617070097", "baseline_ssim_mean": "0.44947243091476097", "remicnet_ssim_mean": "0.4439471835443526"}, {"bucket": "[0.500, 0.750)", "num_samples": "78", "baseline_nmse_mean": "1.0264976185855723", "remicnet_nmse_mean": "1.039713231639559", "baseline_psnr_mean": "30.34447998039117", "remicnet_psnr_mean": "30.292867749041534", "baseline_ssim_mean": "0.49563633165121657", "remicnet_ssim_mean": "0.4928191335410527"}]

## Hardest-Family Results

[{"dataset": "Leave-One-Family-Out Focused OOD", "family": "point_cluster", "num_samples": "100", "baseline_nmse_mean": "1.0174783631864124", "remicnet_nmse_mean": "1.0333975934252673", "baseline_psnr_mean": "31.41709694156296", "remicnet_psnr_mean": "31.351391744085323", "baseline_ssim_mean": "0.5629134932765609", "remicnet_ssim_mean": "0.5599386751182819"}, {"dataset": "Main Test", "family": "point_cluster", "num_samples": "20", "baseline_nmse_mean": "1.0593112634328548", "remicnet_nmse_mean": "1.0816680566713024", "baseline_psnr_mean": "33.750891837221815", "remicnet_psnr_mean": "33.66397591433035", "baseline_ssim_mean": "0.6914872561497153", "remicnet_ssim_mean": "0.6875546811141533"}, {"dataset": "Main Test", "family": "line", "num_samples": "20", "baseline_nmse_mean": "0.9932785535644812", "remicnet_nmse_mean": "0.9804197784430422", "baseline_psnr_mean": "30.700204026090127", "remicnet_psnr_mean": "30.758180959902347", "baseline_ssim_mean": "0.521073577760529", "remicnet_ssim_mean": "0.5281339762832374"}, {"dataset": "Main Test", "family": "L-shape", "num_samples": "20", "baseline_nmse_mean": "0.9796107628174339", "remicnet_nmse_mean": "0.9694901503217672", "baseline_psnr_mean": "28.383145966234007", "remicnet_psnr_mean": "28.42815386597215", "baseline_ssim_mean": "0.3970490986491632", "remicnet_ssim_mean": "0.4038502786665286"}, {"dataset": "Unseen-Parameter OOD", "family": "line", "num_samples": "100", "baseline_nmse_mean": "0.9780945769277153", "remicnet_nmse_mean": "0.96929915196645", "baseline_psnr_mean": "27.09095340443282", "remicnet_psnr_mean": "27.130095628426467", "baseline_ssim_mean": "0.3283020241911921", "remicnet_ssim_mean": "0.3353451777174927"}]

## Visual Outputs

- `viz/progress/curves/baseline_vs_remicnet_main_metrics.png`
- `viz/progress/curves/baseline_vs_remicnet_ood_metrics.png`
- `viz/progress/curves/baseline_vs_remicnet_runtime_speedup.png`
- `viz/progress/curves/grouped_error_by_abs_delta_rho.png`
- `viz/progress/curves/grouped_error_by_abs_pcyc.png`
- `viz/progress/curves/grouped_error_by_pcyc_quarter_pi.png`
- `viz/progress/curves/baseline_vs_remicnet_hardest_families.png`
- `viz/paper_candidates/qualitative/remicnet_best_case_panel.png`
- `viz/paper_candidates/qualitative/remicnet_failure_case_panel.png`

## Git Update Summary

See `git_update_summary_008.md`.

## Remaining Issues

- This repository did not contain a previously trained residual-only baseline checkpoint, so baseline retraining was necessary.
- The current 3D U-Net trunk is shallower than the four-level description in the context docs; the implementation uses the closest compatible RSB-FiLM placement.
- OOD ref3 inputs were recomputed on demand because frozen OOD learning-cache volumes were not present as reusable files.
- The observed gains were not stable across OOD sets, so the current ReMiC-Net variant does not yet provide a clean promotion case.

## Is ReMiC-Net Worth Keeping as Main Method?

No, not as the default main method in its current form. The model produced only slight gains on Main Test and Unseen-Parameter OOD, but it lost on Leave-One-Family-Out OOD, Random-ET OOD, and most grouped mismatch diagnostics. The current evidence supports keeping ReMiC-Net as an exploratory branch rather than replacing the residual baseline.

## Suggested Next Task

Run a controlled ablation on `Mshell`, `delta_rho_raw`, `Pcyc`, and the exact RSB-FiLM insertion pattern while keeping the frozen dataset and ref3 backbone unchanged, to determine whether the weak result is caused by metadata value, modulation strategy, or the shallow trunk mismatch.

## Key file paths for ChatGPT controller

- report: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_008_remicnet_eval/20260511_082329/task_real_008_report.md`
- baseline manifest: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_008_remicnet_eval/20260511_082329/baseline_reference_manifest_008.json`
- input manifest: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_008_remicnet_eval/20260511_082329/remicnet_input_manifest_008.json`
- training metrics: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_008_remicnet_eval/20260511_082329/metrics_remicnet_trainval_008.json`
- main metrics: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_008_remicnet_eval/20260511_082329/metrics_baseline_vs_remicnet_main.csv`
- ood metrics:
  - `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_008_remicnet_eval/20260511_082329/metrics_baseline_vs_remicnet_unseen_param_ood.csv`
  - `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_008_remicnet_eval/20260511_082329/metrics_baseline_vs_remicnet_leave_one_family_out_ood.csv`
  - `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_008_remicnet_eval/20260511_082329/metrics_baseline_vs_remicnet_random_et_ood.csv`
