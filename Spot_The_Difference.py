# HIT137 - Group Assignment 3
# Spot the Difference Game
#
# Group Members:
#   Member 1 - [Ayush Bhusal] : DifferenceRegion class
#   Member 2 - [ROHAN RAI] : ImageProcessor class
#   Member 3 - [AAYUSH BHUSAL] : GUI and Timer
#   Member 4 - [Anurag Deep Silwal] : ScoreTracker class

import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import random
import math
import threading
import pyttsx3



# Class 1 - DifferenceRegion
# CONTRIBUTED BY AYUSH BHUSAL
# This class stores information about one hidden difference

class DifferenceRegion:

    def __init__(self, x, y, width, height, alteration_type):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.alteration_type = alteration_type
        self.found = False
        self.revealed = False

    def get_center(self):
        # calculate center point of the region
        cx = self.x + self.width // 2
        cy = self.y + self.height // 2
        return cx, cy

    def contains_click(self, click_x, click_y, tolerance=35):
        # check if player clicked close enough to this region
        # using pythagorean distance formula
        cx, cy = self.get_center()
        distance = math.sqrt((click_x - cx) ** 2 + (click_y - cy) ** 2)
        return distance <= tolerance

    def get_rect(self):
        return self.x, self.y, self.width, self.height

    def mark_found(self):
        self.found = True

    def mark_revealed(self):
        self.revealed = True

    def is_active(self):
        return not self.found and not self.revealed

    def __str__(self):
        return f"Region at ({self.x},{self.y}) type={self.alteration_type} found={self.found}"

# CLASS 2: ImageProcessor
# CONTRIBUTED BY ROHAN RAI
# DEMONSTRATES : Encapsulation, Polymorphism, and Open Cv operation

class ImageProcessor:

    NUM_DIFFERENCES = 5
    REGION_W = 60
    REGION_H = 60

    def __init__(self):
        self.original_cv = None
        self.modified_cv = None
        self.difference_regions = []

    def load_image(self, filepath):
        # read image from disk using opencv
        try:
            img = cv2.imread(filepath)
            if img is None:
                return False
            self.original_cv = img.copy()
            return True
        except Exception as e:
            print("Error loading image:", e)
            return False

    def generate_differences(self):
        # clone original image and add 5 random non-overlapping shapes
        if self.original_cv is None:
            return []

        self.modified_cv = self.original_cv.copy()
        h, w = self.original_cv.shape[:2]
        self.difference_regions = []

        # list of available shape methods (polymorphism - same signature)
        alteration_types = [
            self._apply_leaf,
            self._apply_cloud,
            self._apply_brush_stroke,
            self._apply_ripple,
            self._apply_sparkle,
        ]

        attempts = 0
        while len(self.difference_regions) < self.NUM_DIFFERENCES and attempts < 500:
            attempts += 1
            rw = self.REGION_W
            rh = self.REGION_H

            if w <= rw + 10 or h <= rh + 10:
                continue

            # pick a random position inside the image
            rx = random.randint(5, w - rw - 5)
            ry = random.randint(5, h - rh - 5)

            candidate = DifferenceRegion(rx, ry, rw, rh, "")

            # skip if this position overlaps an existing region
            if self._overlaps_existing(candidate):
                continue

            # pick a random shape and apply it
            alt_func = random.choice(alteration_types)
            alt_func(rx, ry, rw, rh)
            candidate.alteration_type = alt_func.__name__
            self.difference_regions.append(candidate)

        return self.difference_regions

    def _overlaps_existing(self, candidate, margin=10):
        # check if candidate region overlaps any existing region
        cx1 = candidate.x - margin
        cy1 = candidate.y - margin
        cx2 = candidate.x + candidate.width + margin
        cy2 = candidate.y + candidate.height + margin

        for r in self.difference_regions:
            if cx1 < r.x + r.width and cx2 > r.x and cy1 < r.y + r.height and cy2 > r.y:
                return True
        return False

    # shape 1 - leaf
    def _apply_leaf(self, x, y, w, h):
        cx, cy = x + w // 2, y + h // 2
        mask = np.zeros(self.modified_cv.shape[:2], dtype=np.uint8)
        angle = random.randint(20, 160)

        cv2.ellipse(mask, (cx, cy), (w // 2, h // 4), angle, 0, 360, 255, -1)

        tip_x = int(cx + (w // 2) * math.cos(math.radians(angle)))
        tip_y = int(cy + (w // 2) * math.sin(math.radians(angle)))
        tip_x = max(0, min(self.modified_cv.shape[1] - 1, tip_x))
        tip_y = max(0, min(self.modified_cv.shape[0] - 1, tip_y))

        cv2.ellipse(mask, (tip_x, tip_y), (w // 4, h // 6), angle, 0, 360, 255, -1)

        green_shades = [(34, 139, 34), (0, 128, 0), (85, 107, 47), (107, 142, 35)]
        r, g, b = random.choice(green_shades)
        leaf_colour = np.array([b, g, r], dtype=np.uint8)

        alpha = 0.55
        where = mask > 0
        self.modified_cv[where] = (
            self.modified_cv[where].astype(np.float32) * (1 - alpha)
            + leaf_colour.astype(np.float32) * alpha
        ).astype(np.uint8)

        end_x = int(cx - (w // 2) * math.cos(math.radians(angle)))
        end_y = int(cy - (w // 2) * math.sin(math.radians(angle)))
        cv2.line(self.modified_cv, (tip_x, tip_y), (end_x, end_y), (0, int(g * 0.6), 0), 1)

    # shape 2 - cloud
    def _apply_cloud(self, x, y, w, h):
        overlay = self.modified_cv.copy()
        cx, cy = x + w // 2, y + h // 2
        base_r = w // 4

        for _ in range(random.randint(5, 7)):
            bx = cx + random.randint(-w // 3, w // 3)
            by = cy + random.randint(-h // 4, h // 4)
            br = random.randint(base_r - 4, base_r + 8)
            bx = max(br, min(self.modified_cv.shape[1] - br - 1, bx))
            by = max(br, min(self.modified_cv.shape[0] - br - 1, by))
            shade = random.randint(220, 255)
            cv2.circle(overlay, (bx, by), br, (shade, shade, shade), -1)

        cv2.addWeighted(overlay, 0.50, self.modified_cv, 0.50, 0, self.modified_cv)
        region = self.modified_cv[y:y + h, x:x + w]
        self.modified_cv[y:y + h, x:x + w] = cv2.GaussianBlur(region, (7, 7), 0)

    # shape 3 - brush stroke
    def _apply_brush_stroke(self, x, y, w, h):
        num_pts = random.randint(4, 6)
        pts = []
        for i in range(num_pts):
            px = x + int((w / (num_pts - 1)) * i) + random.randint(-6, 6)
            py = y + h // 2 + random.randint(-h // 3, h // 3)
            px = max(0, min(self.modified_cv.shape[1] - 1, px))
            py = max(0, min(self.modified_cv.shape[0] - 1, py))
            pts.append((px, py))

        paint_colours = [(220, 50, 50), (50, 50, 220), (220, 160, 20), (180, 50, 180), (20, 180, 180)]
        r, g, b = random.choice(paint_colours)
        colour_bgr = (b, g, r)

        overlay = self.modified_cv.copy()
        for i in range(len(pts) - 1):
            t = i / max(len(pts) - 2, 1)
            thickness = int(4 + 8 * math.sin(t * math.pi))
            cv2.line(overlay, pts[i], pts[i + 1], colour_bgr, thickness, cv2.LINE_AA)

        cv2.addWeighted(overlay, 0.65, self.modified_cv, 0.35, 0, self.modified_cv)

    # shape 4 - ripple / water wave effect
    def _apply_ripple(self, x, y, w, h):
        region = self.modified_cv[y:y + h, x:x + w].copy()
        rh, rw = region.shape[:2]
        if rw < 4 or rh < 4:
            return

        amplitude = random.randint(4, 8)
        frequency = random.uniform(0.15, 0.25)

        map_x = np.zeros((rh, rw), dtype=np.float32)
        map_y = np.zeros((rh, rw), dtype=np.float32)

        for row in range(rh):
            for col in range(rw):
                map_x[row, col] = col + amplitude * math.sin(2 * math.pi * frequency * row)
                map_y[row, col] = row + amplitude * math.cos(2 * math.pi * frequency * col)

        map_x = np.clip(map_x, 0, rw - 1).astype(np.float32)
        map_y = np.clip(map_y, 0, rh - 1).astype(np.float32)

        rippled = cv2.remap(region, map_x, map_y, cv2.INTER_LINEAR)
        tint = np.full_like(rippled, (160, 200, 220), dtype=np.uint8)
        rippled = cv2.addWeighted(rippled, 0.80, tint, 0.20, 0)
        self.modified_cv[y:y + h, x:x + w] = rippled

    # shape 5 - sparkle / star
    def _apply_sparkle(self, x, y, w, h):
        cx, cy = x + w // 2, y + h // 2
        outer_r = min(w, h) // 2 - 2
        inner_r = outer_r // 2
        num_points = random.choice([5, 6, 8])

        star_pts = []
        for i in range(num_points * 2):
            angle_deg = (360 / (num_points * 2)) * i - 90
            angle_rad = math.radians(angle_deg)
            r = outer_r if i % 2 == 0 else inner_r
            star_pts.append([int(cx + r * math.cos(angle_rad)),
                             int(cy + r * math.sin(angle_rad))])

        star_pts = np.array([star_pts], dtype=np.int32)
        overlay = self.modified_cv.copy()

        glow_colours = [(255, 255, 150), (200, 230, 255), (255, 200, 255)]
        glow_bgr = random.choice(glow_colours)

        cv2.circle(overlay, (cx, cy), outer_r + 6, glow_bgr, -1)
        cv2.GaussianBlur(overlay, (11, 11), 0, overlay)
        cv2.fillPoly(overlay, star_pts, tuple(min(255, int(c * 1.2)) for c in glow_bgr))

        for i in range(num_points):
            angle_rad = math.radians((360 / num_points) * i - 90)
            ex = int(cx + (outer_r + 4) * math.cos(angle_rad))
            ey = int(cy + (outer_r + 4) * math.sin(angle_rad))
            cv2.line(overlay, (cx, cy), (ex, ey), (255, 255, 255), 1, cv2.LINE_AA)

        cv2.addWeighted(overlay, 0.60, self.modified_cv, 0.40, 0, self.modified_cv)

    def get_display_images(self, max_w, max_h):
        # scale both images to fit the canvas while keeping aspect ratio
        if self.original_cv is None:
            return None, None, 1, 1

        h, w = self.original_cv.shape[:2]
        scale = min(max_w / w, max_h / h, 1.0)
        new_w = int(w * scale)
        new_h = int(h * scale)

        orig_resized = cv2.resize(self.original_cv, (new_w, new_h))
        mod_resized = cv2.resize(self.modified_cv, (new_w, new_h))

        orig_pil = Image.fromarray(cv2.cvtColor(orig_resized, cv2.COLOR_BGR2RGB))
        mod_pil = Image.fromarray(cv2.cvtColor(mod_resized, cv2.COLOR_BGR2RGB))

        return orig_pil, mod_pil, scale, scale

    def draw_circle_on_image(self, pil_img, region, scale_x, scale_y, colour):
        # draw a red or blue circle on the image at the region position
        img_cv = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        cx = int((region.x + region.width // 2) * scale_x)
        cy = int((region.y + region.height // 2) * scale_y)
        radius = int(max(region.width, region.height) // 2 * scale_x) + 5
        bgr = (colour[2], colour[1], colour[0])
        cv2.circle(img_cv, (cx, cy), radius, bgr, 3)
        return Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
