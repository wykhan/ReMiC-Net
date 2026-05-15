

````md
# 005-freeze — Freeze draw005 series and prepare structure-experiment branch

## Task

Only perform git operations. Do not modify code, data, reports, figures, or prompts.

The purpose is to freeze the current draw005-series results and create a clean branch for the upcoming model-structure experiments.

---

## Required git operations

### 1. Check current repository status

```bash
git status
git branch --show-current
git log --oneline -5
````

If there are uncommitted changes, stop and report them. Do not auto-commit unknown changes.

---

### 2. Ensure local master is up to date

```bash
git checkout master
git pull origin master
```

---

### 3. Create an annotated tag for the final draw005 stage

Tag name:

```bash
draw005-final
```

Command:

```bash
git tag -a draw005-final -m "Freeze draw005 series: dense-volume Manisali-style figure, ref31 naming, and true-BP comparison"
```

If the tag already exists, do not overwrite it. Report that it already exists.

Push the tag:

```bash
git push origin draw005-final
```

---

### 4. Create a new branch for model-structure experiments

Branch name:

```bash
task_struc_series
```

Command:

```bash
git checkout -b task_struc_series
```

If the branch already exists locally:

```bash
git checkout task_struc_series
```

If the branch already exists on remote but not locally:

```bash
git fetch origin
git checkout -b task_struc_series origin/task_struc_series
```

Push and set upstream:

```bash
git push -u origin task_struc_series
```

---

### 5. Final verification

Run:

```bash
git status
git branch --show-current
git tag --list | grep draw005-final
git log --oneline -5
```

Expected final state:

```text
current branch: task_struc_series
tag exists: draw005-final
working tree: clean
```

---

## Final report

After execution, report only:

1. whether `draw005-final` tag was created or already existed;
2. whether it was pushed to remote;
3. whether `task_struc_series` branch was created or already existed;
4. whether it was pushed and set to track remote;
5. final `git status` result.

```
```

