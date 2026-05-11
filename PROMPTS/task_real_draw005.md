# task_real_draw005 — Dense-Volume Forward Operator and Manisali-Style 3D Rendering for a Continuous Y-Shaped Target

## Task Title
Develop a dense reflectivity-volume forward operator and redraw a Manisali-style 3D overall imaging figure for a continuous volumetric Y-shaped target.

---

## 1. Background and motivation

In `task_real_draw004`, the generated Y-shaped target still appeared as a set of discrete points in the 3D rendering. This was not acceptable for a Manisali-style overall 3D imaging figure.

The reason was identified as:

1. the Y target was represented as a small list of point scatterers;
2. the 3D visualization used scatter plotting;
3. the target was not a truly dense volumetric reflectivity support;
4. the rendering was not volume rendering / isosurface rendering.

This task corrects that issue.

The goal of `task_real_draw005` is to implement a **dense-volume forward operator** and produce a **continuous Manisali-style 3D overall imaging figure**.

---

## 2. Core decision for this task

This task adopts **方案 B**:

> Develop a dense volume forward operator that directly projects a dense reflectivity volume into synthetic radar echoes.

Do not merely generate a sparse list of point scatterers as the primary scene representation.

The imaging object must be a dense 3D reflectivity volume:

```text
rho[x, y, z] or rho[rho, theta, z]
