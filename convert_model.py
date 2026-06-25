#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Convert my_model.h5 (Keras) to my_model.onnx and validate label parity.

Dev-only: requires tensorflow + tf2onnx + onnxruntime (see requirements-dev.txt).
Never shipped in the release exe. Run once to (re)generate my_model.onnx:

    .\\.venv\\Scripts\\python.exe convert_model.py
"""
import os
import sys

import numpy as np
import tensorflow as tf
import tf2onnx
import onnxruntime as ort

HERE = os.path.dirname(os.path.abspath(__file__))
H5_PATH = os.path.join(HERE, "my_model.h5")
ONNX_PATH = os.path.join(HERE, "my_model.onnx")
SAMPLE_COUNT = 64


def main():
    model = tf.keras.models.load_model(H5_PATH, compile=False)
    input_shape = list(model.inputs[0].shape)  # e.g. [None, 30, 30, 3]
    sample_shape = tuple([1] + input_shape[1:])

    spec = (tf.TensorSpec(sample_shape, tf.float32, name="input"),)
    tf2onnx.convert.from_keras(model, input_signature=spec, opset=13, output_path=ONNX_PATH)

    session = ort.InferenceSession(ONNX_PATH, providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name

    rng = np.random.default_rng(0)
    mismatches = 0
    for _ in range(SAMPLE_COUNT):
        sample = rng.integers(0, 256, size=sample_shape, dtype=np.uint8).astype(np.float32)
        keras_label = int(np.argmax(model.predict(sample, verbose=0)[0]))
        onnx_label = int(np.argmax(session.run(None, {input_name: sample})[0][0]))
        if keras_label != onnx_label:
            mismatches += 1

    if mismatches:
        print(f"PARITY FAILED: {mismatches}/{SAMPLE_COUNT} samples disagreed.")
        print("Do NOT ship ONNX; keep the bundled-TensorFlow fallback.")
        sys.exit(1)

    print(f"Parity OK across {SAMPLE_COUNT} samples.")
    print(f"Wrote {ONNX_PATH}")
    print(f"ONNX input name: {input_name}  shape: {input_shape}")


if __name__ == "__main__":
    main()
