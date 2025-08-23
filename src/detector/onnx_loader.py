# src/detector/onnx_loader.py
import cv2
import numpy as np
import onnxruntime as ort

class YoloOnnx:
    def __init__(self, onnx_path: str, input_size: int = None):
        # --- build session ---
        so = ort.SessionOptions()
        so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_EXTENDED
        # you can tweak threads later; for now we keep defaults
        self.session = ort.InferenceSession(
            onnx_path,
            sess_options=so,
            providers=['CPUExecutionProvider']
        )

        # assume single input, single output
        inp = self.session.get_inputs()[0]
        out = self.session.get_outputs()[0]
        self.input_name = inp.name
        self.output_name = out.name

        # --- introspect input tensor ---
        self.input_shape = list(inp.shape)  # e.g., [1, 3, 640, 640] or [1, 640, 640, 3] or [-1, 3, -1, -1]
        self.input_dtype = str(inp.type)    # e.g., 'tensor(float)'
        self.layout = self._infer_layout(self.input_shape)  # 'NCHW' or 'NHWC'

        # model spatial size (if static). if dynamic, fall back to provided input_size or 640.
        h, w = self._infer_hw(self.input_shape, self.layout)
        if h is not None and w is not None:
            self.model_h = int(h)
            self.model_w = int(w)
        else:
            # dynamic: use caller hint or default
            fallback = input_size or 640
            self.model_h = self.model_w = fallback

        # for clarity elsewhere
        self.input_size = self.model_w if self.model_w == self.model_h else max(self.model_w, self.model_h)

        # normalization/color policy (your model expects 0..1 RGB per your current code)
        self.color = "RGB"
        self.normalize = "/255.0"
        self.dtype = "float32"

        # one clear startup log
        print(
            f"[YoloOnnx] model_input: {self.layout} "
            f"{'x'.join(str(d) for d in self.input_shape)}, "
            f"dtype={self.input_dtype}; using HxW={self.model_h}x{self.model_w}, "
            f"color={self.color}, norm={self.normalize}"
        )

    def _letterbox(self, img, new_w: int, new_h: int):
        h, w = img.shape[:2]
        scale = min(new_w / w, new_h / h)
        nw, nh = int(round(w * scale)), int(round(h * scale))
        resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
        canvas = np.full((new_h, new_w, 3), 114, dtype=np.uint8)
        top = (new_h - nh) // 2
        left = (new_w - nw) // 2
        canvas[top:top+nh, left:left+nw] = resized
        return canvas, scale, left, top

    def infer(self, bgr_img):
        # preprocess (letterbox to model WxH)
        lb, scale, pad_x, pad_y = self._letterbox(bgr_img, self.model_w, self.model_h)
        rgb = cv2.cvtColor(lb, cv2.COLOR_BGR2RGB)
        x = rgb.astype(np.float32) / 255.0

        # layout to match model
        if self.layout == "NCHW":
            x = x.transpose(2, 0, 1)[None]  # (1,3,H,W)
        else:  # NHWC
            x = x[None, ...]                # (1,H,W,3)

        # run
        out = self.session.run([self.output_name], {self.input_name: x})[0]

        # If exported with nms=True, shape is (num_dets, 6): x1,y1,x2,y2,score,class
        dets = out if out.ndim == 2 else out[0]

        if dets.size == 0:
            return np.empty((0,6), dtype=np.float32)

        # map back to original image coords (undo padding/scale)
        dets = dets.copy()
        dets[:, [0,2]] = (dets[:, [0,2]] - pad_x) / (self.model_w / (lb.shape[1])) / (scale)  # robust if non-square
        dets[:, [1,3]] = (dets[:, [1,3]] - pad_y) / (self.model_h / (lb.shape[0])) / (scale)
        # the above keeps intent: subtract pad, then divide by the exact scale used from original -> letterboxed

        return dets  # (N,6)
    
    def _infer_layout(self, shape) -> str:
    # Heuristic: if 3 is at index 1 -> NCHW; if 3 is at last index -> NHWC.
    # If dynamic or ambiguous, default to NCHW (most YOLO exports).
        try:
            if len(shape) == 4:
                if shape[1] == 3:
                    return "NCHW"
                if shape[3] == 3:
                    return "NHWC"
        except Exception:
            pass
        return "NCHW"

    def _infer_hw(self, shape, layout) -> tuple[int, int]:
        if len(shape) != 4:
            return None, None
        # Some models have -1 for dynamic dims
        if layout == "NCHW":
            h, w = shape[2], shape[3]
        else:  # NHWC
            h, w = shape[1], shape[2]
        if isinstance(h, int) and isinstance(w, int) and h > 0 and w > 0:
            return h, w
        return None, None