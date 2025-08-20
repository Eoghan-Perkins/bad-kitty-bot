# src/detector/postprocess.py
import numpy as np

# YOLOv8 class index for 'cat' (COCO) is 15
CAT_CLASS_ID = 15

def filter_cats(dets, conf_thr: float):
    if dets.size == 0:
        return dets
    # dets: [x1,y1,x2,y2,score,class]
    keep = (dets[:,4] >= conf_thr) & (dets[:,5].astype(int) == CAT_CLASS_ID)
    return dets[keep]