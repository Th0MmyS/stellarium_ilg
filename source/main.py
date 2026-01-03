import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import numpy as np
import cv2
import math
import os

class PolarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("360 Polar Mapper - Fixed Colors & Vectors")
        
        # Data
        self.points_logic = []      
        self.ref_horizon = []      
        self.cv_img = None
        self.photo = None          
        self.canvas_size = 800
        self.zoom_factor = 1.0     
        
        # --- UI Layout ---
        self.toolbar = tk.Frame(root, padx=10, pady=10, bg="#f0f0f0")
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        
        tk.Button(self.toolbar, text="1. Load Image", command=self.load_image).pack(side=tk.LEFT, padx=5)
        tk.Button(self.toolbar, text="2. Load Ref", command=self.load_reference).pack(side=tk.LEFT, padx=5)
        
        tk.Label(self.toolbar, text="Zoom:", bg="#f0f0f0").pack(side=tk.LEFT, padx=(20, 5))
        self.zoom_slider = ttk.Scale(self.toolbar, from_=0.5, to=5.0, orient=tk.HORIZONTAL, command=self.update_zoom)
        self.zoom_slider.set(1.0)
        self.zoom_slider.pack(side=tk.LEFT, padx=5)

        self.status_label = tk.Label(self.toolbar, text="Ready", fg="blue", bg="#f0f0f0", font=("Arial", 9, "bold"))
        self.status_label.pack(side=tk.LEFT, padx=20)

        tk.Button(self.toolbar, text="Export (Q)", command=self.export_data, bg="#90ee90").pack(side=tk.RIGHT, padx=5)
        tk.Button(self.toolbar, text="Undo (Z)", command=self.undo).pack(side=tk.RIGHT, padx=5)

        self.main_frame = tk.Frame(root)
        self.main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.main_frame, width=self.canvas_size, height=self.canvas_size, bg="#000", cursor="crosshair")
        self.canvas.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.sidebar = tk.Frame(self.main_frame, width=200, bg="#e0e0e0", padx=5, pady=5)
        self.sidebar.pack(side=tk.RIGHT, fill=tk.Y)
        
        tk.Label(self.sidebar, text="Path Data (CW)", bg="#e0e0e0", font=("Arial", 10, "bold")).pack()
        self.data_display = tk.Text(self.sidebar, font=("Courier", 10), width=18, state='disabled', bg="#f8f8f8")
        self.data_display.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.root.bind("z", lambda e: self.undo())
        self.root.bind("q", lambda e: self.export_data())

    def create_polar_warp(self):
        if self.cv_img is None: return
        h, w = self.cv_img.shape[:2]
        size = self.canvas_size
        range_val = np.linspace(-1, 1, size)
        x, y = np.meshgrid(range_val, range_val)
        
        r = np.sqrt(x**2 + y**2) / self.zoom_factor
        theta = np.arctan2(y, x) 
        
        map_y = (r * h).astype(np.float32)
        map_x = (((theta + np.pi/2) % (2*np.pi)) / (2*np.pi) * w).astype(np.float32)
        
        # Perform Warp
        polar_cv = cv2.remap(self.cv_img, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0))
        
        # --- COLOR FIX ---
        # Convert BGR (OpenCV) to RGB (PIL/Tkinter)
        polar_rgb = cv2.cvtColor(polar_cv, cv2.COLOR_BGR2RGB)
        
        self.photo = ImageTk.PhotoImage(Image.fromarray(polar_rgb))

    def on_mouse_move(self, event):
        if self.photo is None: return
        self.refresh_canvas()
        cx, cy = self.canvas_size // 2, self.canvas_size // 2
        
        # Dynamic line from center to mouse
        self.canvas.create_line(cx, cy, event.x, event.y, fill="cyan", width=1, dash=(2,2))
        
        dx, dy = event.x - cx, event.y - cy
        angle = (math.degrees(math.atan2(-dx, dy)) + 360) % 360
        self.status_label.config(text=f"Mouse Angle: {int(angle)}°")

    def on_click(self, event):
        if self.cv_img is None: return
        cx, cy = self.canvas_size // 2, self.canvas_size // 2
        dx, dy = event.x - cx, event.y - cy
        radius = math.sqrt(dx**2 + dy**2)
        norm_r = (radius / (self.canvas_size / 2)) / self.zoom_factor
        angle = (math.degrees(math.atan2(-dx, dy)) + 360) % 360
        
        if self.points_logic:
            last_angle = self.points_logic[-1][0]
            if angle <= last_angle:
                self.status_label.config(text=f"ERROR: Go Clockwise (> {int(last_angle)}°)", fg="red")
                return

        elevation = (0.5 - norm_r) * 180 
        self.points_logic.append([angle, elevation])
        self.update_sidebar()
        self.refresh_canvas()

    def refresh_canvas(self):
        if self.photo is None: return
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        cx, cy = self.canvas_size // 2, self.canvas_size // 2
        
        # Visual Guides
        self.canvas.create_line(cx, cy, cx, self.canvas_size, fill="yellow", width=2, arrow=tk.LAST)
        r_mid = (0.5 * self.zoom_factor) * (self.canvas_size / 2)
        self.canvas.create_oval(cx-r_mid, cy-r_mid, cx+r_mid, cy+r_mid, outline="white", width=1, dash=(5,5))
        
        lbls = [("N", 0), ("E", 90), ("S", 180), ("W", 270)]
        for txt, ang in lbls:
            rad = math.radians(ang)
            tx = cx - (self.canvas_size/2 - 25) * math.sin(rad)
            ty = cy + (self.canvas_size/2 - 25) * math.cos(rad)
            self.canvas.create_text(tx, ty, text=txt, fill="yellow" if ang==0 else "white", font=("Arial", 10, "bold"))

        if self.ref_horizon: self.draw_path(self.ref_horizon, "red", is_dash=True)
        if self.points_logic: self.draw_path(self.points_logic, "cyan", is_dash=False)

    def draw_path(self, data_list, color, is_dash=False):
        cx, cy = self.canvas_size // 2, self.canvas_size // 2
        pixels = []
        for row in data_list:
            ang, elev = row[0], row[1]
            norm_r = 0.5 - (elev / 180.0)
            pix_r = norm_r * (self.canvas_size / 2) * self.zoom_factor
            rad = math.radians(ang)
            px = cx - pix_r * math.sin(rad)
            py = cy + pix_r * math.cos(rad)
            pixels.append((px, py))
        for i in range(len(pixels)-1):
            self.canvas.create_line(pixels[i], pixels[i+1], fill=color, width=2, dash=(4,4) if is_dash else None)
        if not is_dash:
            for px, py in pixels:
                self.canvas.create_oval(px-3, py-3, px+3, py+3, fill=color, outline="black")

    def load_image(self):
        path = filedialog.askopenfilename()
        if not path: return
        self.cv_img = cv2.imread(path)
        self.points_logic = []
        self.create_polar_warp(); self.refresh_canvas()

    def update_sidebar(self):
        self.data_display.config(state='normal')
        self.data_display.delete('1.0', tk.END)
        for row in self.points_logic:
            self.data_display.insert(tk.END, f"{int(round(row[0]))} {int(round(row[1]))}\n")
        self.data_display.config(state='disabled')

    def load_reference(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if not path: return
        try:
            self.ref_horizon = np.loadtxt(path).tolist()
            self.refresh_canvas()
        except: pass

    def update_zoom(self, val):
        self.zoom_factor = float(val)
        if self.cv_img is not None:
            self.create_polar_warp(); self.refresh_canvas()

    def undo(self):
        if self.points_logic: self.points_logic.pop(); self.update_sidebar(); self.refresh_canvas()

    def export_data(self):
        content = self.data_display.get('1.0', tk.END).strip()
        if not content: return
        for f in ["horizon.txt"]:
            with open(f, "w") as file: file.write(content + "\n")
        messagebox.showinfo("Exported", "Saved successfully.")

if __name__ == "__main__":
    root = tk.Tk(); app = PolarApp(root); root.mainloop()