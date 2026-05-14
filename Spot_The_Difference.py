# HIT137 - Group Assignment 3
# Spot the Difference Game
#
# Group Members:
#   Member 1 - [Ayush Bhusal] : DifferenceRegion class
#   Member 2 - [ROHAN RAI] : ImageProcessor class
#   Member 3 - [AAYUSH KC] : GUI and Timer
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

# Class 3 - ScoreTracker
# contributor: Aayush KC
# This class keeps track of score, mistakes and game state

class ScoreTracker:

    MAX_MISTAKES = 3
    TOTAL_DIFFERENCES = 5

    def __init__(self):
        self.total_found = 0
        self.mistakes = 0
        self.locked = False
        self.current_image_found = 0
        self.image_history = []

    def record_find(self):
        # player found a difference
        try:
            self.total_found += 1
            self.current_image_found += 1
            return self.total_found
        except Exception as e:
            print("Error in record_find:", e)
            return self.total_found

    def record_mistake(self):
        # player clicked wrong area
        try:
            self.mistakes += 1
            if self.mistakes >= self.MAX_MISTAKES:
                self.locked = True
            return self.locked
        except Exception as e:
            print("Error in record_mistake:", e)
            return self.locked

    def reset_for_new_image(self):
        # save current image result then reset for next image
        try:
            if self.current_image_found > 0 or self.mistakes > 0:
                self.image_history.append({
                    'found': self.current_image_found,
                    'mistakes': self.mistakes,
                    'completed': self.current_image_found >= self.TOTAL_DIFFERENCES
                })
            self.mistakes = 0
            self.locked = False
            self.current_image_found = 0
        except Exception as e:
            print("Error in reset:", e)
            self.mistakes = 0
            self.locked = False

    def is_locked(self):
        return self.locked

    def get_mistakes(self):
        return self.mistakes

    def get_total_found(self):
        return self.total_found

    def get_mistakes_remaining(self):
        return max(0, self.MAX_MISTAKES - self.mistakes)

    def __str__(self):
        return f"ScoreTracker(total={self.total_found}, mistakes={self.mistakes}/{self.MAX_MISTAKES}, locked={self.locked})"
    
    
# Class 4 - SpotTheDifferenceApp
# contributed by Anurag Deep Silwal
# Main application window - inherits from tk.Tk
# This class manages the GUI and connects all other classes

class SpotTheDifferenceApp(tk.Tk):

    CANVAS_W = 500
    CANVAS_H = 420

    def __init__(self):
        # call parent class constructor (tk.Tk) - this creates the window
        super().__init__()
        self.title("HIT137 - Spot the Difference")
        self.resizable(False, False)
        self.config(bg="#1e1e2e")

        # create processor and tracker objects (composition)
        self.processor = ImageProcessor()
        self.tracker = ScoreTracker()

        # variables for displaying images
        self.orig_photo = None
        self.mod_photo = None
        self.scale_x = 1.0
        self.scale_y = 1.0

        # timer variables
        self.timer_seconds = 0
        self.timer_running = False
        self.image_count = 0
        self.best_time = None
        self._timer_id = None

        self._build_ui()

    def _build_ui(self):
        # create all the widgets for the window

        # title label at the top
        top_frame = tk.Frame(self, bg="#1e1e2e")
        top_frame.grid(row=0, column=0, columnspan=2, pady=(12, 4), padx=12)

        tk.Label(top_frame, text="Spot the Difference",
                 font=("Arial", 20, "bold"), fg="#cba6f7", bg="#1e1e2e").pack()

        # stats bar showing remaining, mistakes, score, timer
        stats_frame = tk.Frame(self, bg="#313244")
        stats_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=4)

        self.remaining_var = tk.StringVar(value="Remaining: -")
        self.mistakes_var = tk.StringVar(value="Mistakes: 0 / 3")
        self.score_var = tk.StringVar(value="Total Found: 0")
        self.timer_var = tk.StringVar(value="Time: 0s")
        self.image_count_var = tk.StringVar(value="Image: 0")
        self.best_time_var = tk.StringVar(value="Best: --")

        lbl_style = dict(font=("Arial", 11, "bold"), bg="#313244", fg="#cdd6f4", padx=10, pady=6)

        tk.Label(stats_frame, textvariable=self.remaining_var, **lbl_style).grid(row=0, column=0)
        tk.Label(stats_frame, textvariable=self.mistakes_var, **lbl_style).grid(row=0, column=1)
        tk.Label(stats_frame, textvariable=self.score_var, **lbl_style).grid(row=0, column=2)
        tk.Label(stats_frame, textvariable=self.timer_var, **lbl_style).grid(row=0, column=3)
        tk.Label(stats_frame, textvariable=self.image_count_var, **lbl_style).grid(row=0, column=4)
        tk.Label(stats_frame, textvariable=self.best_time_var, **lbl_style).grid(row=0, column=5)

        self.status_lbl = tk.Label(stats_frame, text="Load an image to start!",
                                   font=("Arial", 11), fg="#f38ba8", bg="#313244", padx=10)
        self.status_lbl.grid(row=1, column=0, columnspan=6, pady=(0, 4))

        # canvas area for displaying images side by side
        canvas_frame = tk.Frame(self, bg="#1e1e2e")
        canvas_frame.grid(row=2, column=0, columnspan=2, padx=12, pady=8)

        tk.Label(canvas_frame, text="Original", font=("Arial", 11, "bold"),
                 fg="#a6e3a1", bg="#1e1e2e").grid(row=0, column=0, pady=(0, 2))
        tk.Label(canvas_frame, text="Modified  (click here!)", font=("Arial", 11, "bold"),
                 fg="#fab387", bg="#1e1e2e").grid(row=0, column=1, pady=(0, 2))

        self.orig_canvas = tk.Canvas(canvas_frame, width=self.CANVAS_W,
                                     height=self.CANVAS_H, bg="#181825",
                                     highlightthickness=2, highlightbackground="#585b70")
        self.orig_canvas.grid(row=1, column=0, padx=(0, 8))

        self.mod_canvas = tk.Canvas(canvas_frame, width=self.CANVAS_W,
                                    height=self.CANVAS_H, bg="#181825",
                                    highlightthickness=2, highlightbackground="#fab387",
                                    cursor="crosshair")
        self.mod_canvas.grid(row=1, column=1, padx=(8, 0))

        # bind mouse click to the modified canvas only
        self.mod_canvas.bind("<Button-1>", self._on_canvas_click)
        self._show_placeholder()

        # buttons at the bottom
        btn_frame = tk.Frame(self, bg="#1e1e2e")
        btn_frame.grid(row=3, column=0, columnspan=2, pady=(4, 14))

        btn_style = dict(font=("Arial", 12, "bold"), width=18, pady=6, relief="flat", cursor="hand2")

        self.load_btn = tk.Button(btn_frame, text="Load Image",
                                  bg="#cba6f7", fg="#1e1e2e",
                                  command=self._load_image, **btn_style)
        self.load_btn.grid(row=0, column=0, padx=10)

        self.reveal_btn = tk.Button(btn_frame, text="Reveal All",
                                    bg="#f38ba8", fg="#1e1e2e",
                                    command=self._reveal_all,
                                    state=tk.DISABLED, **btn_style)
        self.reveal_btn.grid(row=0, column=1, padx=10)

    def _show_placeholder(self):
        # show placeholder text on both canvases before image is loaded
        for canvas, text in [
            (self.orig_canvas, "Original image\nappears here"),
            (self.mod_canvas, "Modified image\nappears here\n\nclick to play")
        ]:
            canvas.delete("all")
            canvas.create_text(self.CANVAS_W // 2, self.CANVAS_H // 2,
                               text=text, fill="#585b70",
                               font=("Arial", 14), justify="center")

    def _load_image(self):
        # open file dialog and load selected image
        filepath = filedialog.askopenfilename(
            title="Choose an image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")]
        )
        if not filepath:
            return

        if not self.processor.load_image(filepath):
            messagebox.showerror("Error", "Could not load image.")
            return

        self.processor.generate_differences()
        self.tracker.reset_for_new_image()

        # update image counter and start timer
        self.image_count += 1
        self.image_count_var.set(f"Image: {self.image_count}")
        self._start_timer()

        self._render_images()
        self._update_stats()
        self._set_status("Find all 5 differences!")
        self.reveal_btn.config(state=tk.NORMAL)
        self.mod_canvas.config(highlightbackground="#fab387")

    def _render_images(self):
        # get scaled images and draw them on the canvases
        orig_pil, mod_pil, sx, sy = self.processor.get_display_images(self.CANVAS_W, self.CANVAS_H)
        if orig_pil is None:
            return
        self.scale_x = sx
        self.scale_y = sy
        self._draw_on_canvas(self.orig_canvas, orig_pil)
        self._draw_on_canvas(self.mod_canvas, mod_pil)

    def _draw_on_canvas(self, canvas, pil_img):
        # draw a PIL image onto a canvas widget
        photo = ImageTk.PhotoImage(pil_img)
        canvas.delete("all")
        canvas.create_image(self.CANVAS_W // 2, self.CANVAS_H // 2, image=photo, anchor="center")
        # save reference so image doesn't get deleted by garbage collector
        if canvas == self.orig_canvas:
            self.orig_photo = photo
        else:
            self.mod_photo = photo

    def _redraw_circles(self):
        # redraw images and put circles on found or revealed regions
        orig_pil, mod_pil, sx, sy = self.processor.get_display_images(self.CANVAS_W, self.CANVAS_H)
        if orig_pil is None:
            return
        self.scale_x = sx
        self.scale_y = sy
        for region in self.processor.difference_regions:
            if region.found:
                colour = (255, 50, 50)      # red circle for found
            elif region.revealed:
                colour = (50, 100, 255)     # blue circle for revealed
            else:
                continue
            orig_pil = self.processor.draw_circle_on_image(orig_pil, region, sx, sy, colour)
            mod_pil = self.processor.draw_circle_on_image(mod_pil, region, sx, sy, colour)
        self._draw_on_canvas(self.orig_canvas, orig_pil)
        self._draw_on_canvas(self.mod_canvas, mod_pil)

    def _on_canvas_click(self, event):
        # handle click on the modified canvas
        if self.tracker.is_locked():
            return
        if self.processor.original_cv is None:
            return
        if sum(1 for r in self.processor.difference_regions if not r.found) == 0:
            return

        # convert canvas click position to original image position
        orig_pil, _, sx, sy = self.processor.get_display_images(self.CANVAS_W, self.CANVAS_H)
        img_w, img_h = orig_pil.size
        offset_x = (self.CANVAS_W - img_w) // 2
        offset_y = (self.CANVAS_H - img_h) // 2
        img_click_x = (event.x - offset_x) / sx
        img_click_y = (event.y - offset_y) / sy

        # check if click matches any unfound region
        hit = False
        for region in self.processor.difference_regions:
            if region.found:
                continue
            if region.contains_click(img_click_x, img_click_y):
                region.mark_found()
                self.tracker.record_find()
                hit = True
                self._redraw_circles()
                self._update_stats()
                self._check_completion()
                break

        if not hit:
            locked = self.tracker.record_mistake()
            self._update_stats()
            remaining = self.tracker.get_mistakes_remaining()
            if locked:
                self._stop_timer()
                found = sum(1 for r in self.processor.difference_regions if r.found)
                self._set_status(f"3 mistakes! {found}/5 found. Load a new image.", colour="#f38ba8")
                self.mod_canvas.config(highlightbackground="#f38ba8")
            else:
                self._set_status(f"Wrong! {remaining} mistake(s) remaining.", colour="#fab387")

    def _check_completion(self):
        # check if all 5 differences have been found
        remaining = sum(1 for r in self.processor.difference_regions if not r.found)
        if remaining == 0:
            self._stop_timer()
            elapsed = self.timer_seconds

            # update best time if this is the fastest completion
            if self.best_time is None or elapsed < self.best_time:
                self.best_time = elapsed
                self.best_time_var.set(f"Best: {self._format_time(elapsed)}")

            self._set_status("All 5 found! Load another image to continue.", colour="#a6e3a1")
            self._speak("Hurray! You have found all the differences. Well done!")
            messagebox.showinfo("Well done!",
                                f"You found all 5 differences!\n"
                                f"Time: {self._format_time(elapsed)}\n"
                                f"Total found this session: {self.tracker.get_total_found()}")

    def _reveal_all(self):
        # reveal all unfound differences with blue circles
        if self.processor.original_cv is None:
            return
        self._stop_timer()
        for region in self.processor.difference_regions:
            if not region.found:
                region.mark_revealed()
        self._redraw_circles()
        self.remaining_var.set("Remaining: 0")
        self._set_status("Differences revealed in blue. Load a new image.", colour="#89dceb")

    def _update_stats(self):
        # update all the stats labels on screen
        remaining = sum(1 for r in self.processor.difference_regions if not r.found)
        self.remaining_var.set(f"Remaining: {remaining}")
        self.mistakes_var.set(f"Mistakes: {self.tracker.get_mistakes()} / 3")
        self.score_var.set(f"Total Found: {self.tracker.get_total_found()}")

    def _set_status(self, text, colour="#cdd6f4"):
        self.status_lbl.config(text=text, fg=colour)

    def _speak(self, message):
        # speak a message using text to speech in background thread
        def run():
            try:
                engine = pyttsx3.init()
                engine.setProperty('rate', 145)
                engine.setProperty('volume', 1.0)
                engine.say(message)
                engine.runAndWait()
                engine.stop()
            except Exception as e:
                print("TTS error:", e)
        threading.Thread(target=run, daemon=True).start()

    def _start_timer(self):
        # start the timer from 0
        self._stop_timer()
        self.timer_seconds = 0
        self.timer_var.set("Time: 0s")
        self.timer_running = True
        self._tick()

    def _tick(self):
        # called every second to update the timer
        if self.timer_running:
            self.timer_seconds += 1
            self.timer_var.set(f"Time: {self._format_time(self.timer_seconds)}")
            self._timer_id = self.after(1000, self._tick)

    def _stop_timer(self):
        # stop the timer
        self.timer_running = False
        if self._timer_id:
            try:
                self.after_cancel(self._timer_id)
            except Exception:
                pass

    def _format_time(self, seconds):
        # convert seconds into readable format
        if seconds < 60:
            return f"{seconds}s"
        return f"{seconds // 60}m {seconds % 60}s"


# run the application
if __name__ == "__main__":
    app = SpotTheDifferenceApp()
    app.mainloop()