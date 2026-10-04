onnxruntime-web 1.30.0 runtime files, copied unchanged from node_modules/onnxruntime-web/dist/ (MIT licence, Microsoft):
  ort-wasm-simd-threaded.wasm   WebAssembly runtime (CPU/WASM provider), 14.2 MB
  ort-wasm-simd-threaded.mjs    its JavaScript loader
Used by app/src/vision/segmentModel.ts through ort.env.wasm.wasmPaths, single thread (no cross-origin isolation needed).
To update: copy the two files again after upgrading the onnxruntime-web package, and bump VERSION in public/sw.js.
