# dataset_protocol

## Role

This document freezes the point-target dataset protocol for `task_real_002`.
It does not replace the future extended-target dataset protocol, which must be frozen separately in a later task.

## Scope

- This version freezes only the point-target protocol
- Extended-target family protocol remains pending
- Manisali-style random ET protocol remains pending

## Dataset Splits

### Target Formal Scale

- `train = 6000`
- `val = 1000`
- `test = 1000`

### Smoke Scale

- `smoke_train = 64`
- `smoke_val = 16`
- `smoke_test = 16`

The smoke scale is the default execution scale for `task_real_002`, while the builder keeps support for the formal split sizes.

## Scene Type Coverage

Each split must cover:

- single-point scenes
- double-point scenes
- small multi-point scenes with `3` to `5` points

## Spatial Coverage

Point placement must explicitly cover:

- different radial locations within the protocol envelope
- different height locations within the protocol envelope
- different azimuth locations around the cylindrical scan
- different inter-point distances
- both near-boundary and non-boundary placements

The builder should use protocol-consistent grid spacing and keep all points inside the valid scene envelope.

## Ground Truth Definition

- Ground truth is the voxel-space amplitude volume
- The current phase does not use complex-valued supervision
- The label must never be replaced by a BP image

## Scatterer Coefficient Rule

This task freezes a simple consistent rule:

- amplitude is sampled independently from a bounded real interval `[0.8, 1.2]`
- phase randomization is disabled
- the complex scatter coefficient is therefore real-valued and non-negative

This rule keeps the smoke validation interpretable and must be recorded in the sample metadata.

## Voxel Grid And Scene Envelope

The point-target dataset must remain consistent with `CONTEXT/simulation_protocol.md`:

- cylindrical scan radius `R = 0.6 m`
- scene radius `X0 = 0.3 m`
- scene height `H = 2.0 m`
- Cartesian voxel spacing `5 mm` in `x/y`
- height spacing `4 mm` in `z`

Implementations may reconstruct protocol-consistent local ROIs during smoke validation, but those ROIs must use the frozen grid spacing and stay inside the frozen envelope.

## Metadata Requirements

Every sample must record at least:

- sample id
- split
- seed
- point count
- point positions
- amplitudes
- whether the sample belongs to smoke scale or formal scale

## Current Task Boundary

This dataset protocol is frozen for point-target physical-chain validation only.
It does not authorize ET generation, physics consistency, or final paper-scale training.
