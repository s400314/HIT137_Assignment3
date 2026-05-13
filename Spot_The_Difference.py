# HIT137 - Group Assignment 3
# Spot the Difference Game
#
# Group Members:
#   Member 1 - [Ayush Bhusal] : DifferenceRegion class
#   Member 2 - [Aayush KC] : ImageProcessor class
#   Member 3 - [Rohan Rai] : GUI and Timer
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

