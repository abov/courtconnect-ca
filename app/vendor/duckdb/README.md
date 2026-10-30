# Vendored files for ask-the-data.html

Copied here so the page makes no request to another site. Fetched 2026-10-29 from jsDelivr with the project User-Agent; `SHA256SUMS` pins them and `ci/check_ask_the_data.py` verifies it.

- `duckdb-eh.wasm`, `duckdb-browser-eh.worker.js`, `duckdb-browser.mjs`: `@duckdb/duckdb-wasm@1.29.0` (MIT). The `eh` build needs WebAssembly exception handling (current Chrome, Edge, Firefox, Safari); the 40 MB `mvp` fallback is not included.
- `apache-arrow.mjs`: `apache-arrow@17.0.0` (Apache-2.0), jsDelivr's single-file ESM bundle. Its two absolute imports were rewritten to the relative files below, which is the only edit.
- `flatbuffers.mjs` (`flatbuffers@24.3.25`, Apache-2.0) and `tslib.mjs` (`tslib@2.6.3`, 0BSD): dependencies of the arrow bundle, unedited.

To upgrade: download the new versions, redo the import rewrite, regenerate `SHA256SUMS` (`sha256sum <files> > SHA256SUMS`), and re-run `python ci/check_ask_the_data.py`.
