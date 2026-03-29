# Public Benchmark Helper

This folder contains a simple script for repeating the public `maxpack pack` smoke flow on your own data.

## Quick start

If `maxpack` is already installed and available in `PATH`:

```bash
python3 benchmarks/smoke_pack.py /path/to/dataset
```

Or with an explicit binary path:

```bash
python3 benchmarks/smoke_pack.py --binary ./maxpack-darwin-arm64 /path/to/dataset
```

Default settings match the public maxpack benchmark settings:

- `--mode fast`
- `--global-zstd-level 3`
- `--warmups 1`
- `--runs 2`

This public smoke helper does not pin threads by itself. If you want to mirror the headline
CPython/Go protocol more closely, run it with `MAXPACK_THREADS=4`.

The script prints:

- median wall time
- best run
- archive size
- ratio
- peak RSS

It is intentionally a maxpack-side smoke helper, not a full competitor harness for every chart in the article.
