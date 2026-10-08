# f8pydl

This repository owns its source, tests, `extension.json`, service manifests and model metadata.
The Studio superbuild can check it out unchanged at `extensions/f8pydl`.

The SDK source revision used by CI is `d0485cf6c8a7b7c0a9e2506101c781ee585695c0`. Checkout `feel8-fun/f8sdk` at that
revision into `.sdk` before `pixi install`; only the public SDK is a runtime dependency.
Use the commands in `.github/workflows/quality.yml` for local build/test parity.

Python releases contain this package's wheel contents and its publisher-owned locked
workspace. Environment names and counts are local publisher choices; `extension.json`
selects the default environment. The SDK builder converts source `workspace` inputs
to an independent Pixi runtime, or accepts a prepared `--runtime-root`. Native releases contain deployed executables and their runtime
libraries. `python -m f8pysdk.extension_packaging` verifies the real `--describe` entrypoints,
then produces an importable ZIP and its SHA-256. No editable source path is included.

The initial source export is a snapshot. Original commit history remains in the superbuild;
use `git subtree split --prefix=extensions/f8pydl` if full package history is needed.

Service manifests use named package, bundle, and writable roots. See the [SDK service path contract](https://github.com/feel8-fun/f8sdk/blob/d0485cf6c8a7b7c0a9e2506101c781ee585695c0/docs/service-paths.md). Package metadata stays inside the installation; user models and settings use separate writable roots.
