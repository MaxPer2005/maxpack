# maxpack

**Deduplicating archiver for versioned data.**

Packs multiple versions of a project into a single archive, achieving 5-20x better compression than tar+zstd by eliminating inter-version redundancy. Uses a proprietary deduplication and compression pipeline optimized for versioned data.

## Benchmarks

Compression ratio (higher = better) on real-world versioned datasets:

| Dataset | Input Size | maxpack | tar+zstd | 7z -mx=9 | tar+xz | tar+lz4 | zip |
|---------|-----------|---------|----------|----------|--------|---------|-----|
| lsd | 4 MB | **31.9x** | 15.4x | 34.9x | 30.7x | 3.1x | 3.9x |
| fd | 4 MB | **27.9x** | 12.5x | 30.1x | 27.2x | 2.7x | 3.7x |
| bat | 56 MB | **11.3x** | 3.3x | 14.6x | 4.0x | 2.5x | 2.9x |
| go | 911 MB | **20.2x** | 4.5x | 12.8x | 6.2x | 2.6x | 3.4x |
| cpython | 964 MB | **13.4x** | 3.7x | 10.1x | 4.8x | 2.4x | 3.3x |
| **all** | **1.9 GB** | **15.5x** | 4.1x | 11.6x | 5.3x | 2.5x | 3.3x |

On large datasets (>100 MB), maxpack dominates both ratio and speed:

**go** (911 MB, 10 versions):

| | maxpack | 7z -mx=9 | tar+xz |
|---|---------|----------|--------|
| **Ratio** | **20.2x** | 12.8x | 6.2x |
| **Pack time** | **6.4s** | 79.8s | 242.7s |
| **Unpack time** | **5.4s** | 11.8s | 42.9s |
| **Pack speed** | **142 MB/s** | 11.4 MB/s | 3.8 MB/s |

**cpython** (964 MB, 10 versions):

| | maxpack | 7z -mx=9 | tar+xz |
|---|---------|----------|--------|
| **Ratio** | **13.4x** | 10.1x | 4.8x |
| **Pack time** | **4.4s** | 94.5s | 221.9s |
| **Unpack time** | **2.6s** | 5.0s | 22.8s |
| **Pack speed** | **220 MB/s** | 10.2 MB/s | 4.3 MB/s |

**all** (1.9 GB, all datasets combined):

| | maxpack | 7z -mx=9 | tar+xz |
|---|---------|----------|--------|
| **Ratio** | **15.5x** | 11.6x | 5.3x |
| **Pack time** | **14.1s** | 249.1s | 483.0s |
| **Unpack time** | **8.4s** | 17.3s | 67.0s |
| **Pack speed** | **135 MB/s** | 7.8 MB/s | 4.0 MB/s |

![Compression metrics across datasets](benchmarks_curves.png)

## Integration

maxpack exposes a C-compatible FFI interface (`maxpack.h`) for embedding the compression engine directly into your applications. Bind it from Python, Go, C++, or any language with C FFI support.

## Install

### Quick install (macOS & Linux)

```bash
curl -fsSL https://raw.githubusercontent.com/MaxPer2005/maxpack/main/install.sh | sh
```

### Manual download

Download the binary for your platform from [Releases](https://github.com/MaxPer2005/maxpack/releases/latest):

| Platform | Binary |
|----------|--------|
| macOS (Apple Silicon) | `maxpack-darwin-arm64` |
| Linux x86_64 | `maxpack-linux-amd64` |

```bash
chmod +x maxpack-*
sudo mv maxpack-* /usr/local/bin/maxpack
```

**macOS note:** If you get "cannot be opened because the developer cannot be verified", run:
```bash
xattr -d com.apple.quarantine /usr/local/bin/maxpack
```

## Quick Start

**Pack** multiple versions of a project:

```bash
maxpack pack --output project.maxpack ./v1.0 ./v1.1 ./v1.2
```

**Unpack** an archive:

```bash
maxpack unpack project.maxpack --output ./restored
```

**Inspect** archive contents:

```bash
maxpack info project.maxpack
```

On first run, you'll be asked to accept the license agreement. You can also accept non-interactively:

```bash
maxpack --accept-license pack --output project.maxpack ./data
```

## License

maxpack is proprietary software. Free for personal, non-commercial use up to 50 GB cumulative input data. Unpacking is always free regardless of volume.

Commercial use requires a separate license. Contact: wundel.max@gmail.com

See [LICENSE.md](LICENSE.md) for the full End-User License Agreement.
