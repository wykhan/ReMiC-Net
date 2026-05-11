# project_brief

## Core Research Question

The project asks whether physics-guided learning under real cylindrical aperture simulation can preserve the low complexity of reduced-reference imaging while materially improving reconstruction quality, especially for extended targets.

## Why This Is Not Pure Black-Box Reconstruction

The repository follows a physics-backbone-first route rather than raw-echo-to-image end-to-end regression. The first stage remains a physically meaningful cylindrical imaging operator, and learning is used as controlled refinement on top of that backbone.

## Why Restart From Real Cylindrical Physics Simulation

The project explicitly does not inherit old proxy datasets or conclusions based on incorrect or incomplete geometry. It restarts from true cylindrical geometry, true forward echo simulation, and a consistent traditional reconstruction chain defined by the frozen protocol documents.

## Why Point Targets Are Only a Prerequisite

Point targets are used to verify the physical chain, geometric consistency, and reduced-reference error behavior. They are necessary but not sufficient for the paper claim. The main scientific battlefield is extended-target imaging, where structure recovery and approximation compensation matter most.

## Why Stage One Uses Reduced-Reference Physical Backbone by Default

The default first-stage backbone is `ref3`, because it is the most compressed baseline that still preserves physical meaning and therefore best tests the speed-quality trade-off. It is also the default reduced-reference backbone frozen by the reference-surface strategy.

## Current Accelerated Front-End Freeze

After wrap hardening, the repository-level default accelerated front-end is frozen as `Variant B`, meaning:

- active azimuth-height windows
- MATLAB-inspired full-library sinc geometry correction

Dense global tensor mode is retained only for audit/debug comparisons and is not the default path for validation or ET entry.

## Why Stage Two Uses a Manisali-Style 3D U-Net

The second stage is a Manisali-style 3D U-Net refiner because the project needs object-space compensation of approximation error rather than unconstrained hallucination. This aligns the learning stage with prior physics-guided 3D reconstruction logic while adapting the physical front end to cylindrical imaging.

## Current Task Boundary

Current work is bootstrap only. The repository is being prepared for reproducible follow-up tasks, without launching formal simulation, dataset generation, benchmark runs, or model training.
