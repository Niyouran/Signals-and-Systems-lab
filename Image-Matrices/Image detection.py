import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk, ImageOps, ImageFilter
import numpy as np
import cv2

class ImageProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Processor")
        self.root.geometry("1200x800")
        
        # 初始化变量
        self.original_image = None
        self.processed_image = None
        self.display_ratio = 1.0
        
        # 创建界面布局
        self.create_widgets()
        self.create_menu()
        
    def create_widgets(self):
        # 控制面板
        control_frame = ttk.Frame(self.root, width=200)
        control_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        # 图像显示区域
        self.image_frame = ttk.Frame(self.root)
        self.image_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
        
        # 原图画布
        self.original_canvas = tk.Canvas(self.image_frame, width=600, height=600)
        self.original_canvas.pack(side=tk.LEFT, expand=True)
        
        # 处理结果画布
        self.processed_canvas = tk.Canvas(self.image_frame, width=600, height=600)
        self.processed_canvas.pack(side=tk.RIGHT, expand=True)
        
        # 控制按钮
        ttk.Button(control_frame, text="打开图像", command=self.open_image).pack(pady=5)
        ttk.Button(control_frame, text="保存结果", command=self.save_image).pack(pady=5)
        ttk.Button(control_frame, text="灰度转换", command=self.convert_grayscale).pack(pady=5)
        ttk.Button(control_frame, text="亮度对比度", command=self.adjust_brightness_contrast).pack(pady=5)
        ttk.Button(control_frame, text="伽马校正", command=self.gamma_correction).pack(pady=5)
        ttk.Button(control_frame, text="水平翻转", command=lambda: self.flip_image(horizontal=True)).pack(pady=5)
        ttk.Button(control_frame, text="垂直翻转", command=lambda: self.flip_image(horizontal=False)).pack(pady=5)
        ttk.Button(control_frame, text="高斯模糊", command=self.gaussian_blur).pack(pady=5)
        ttk.Button(control_frame, text="边缘检测", command=self.edge_detection).pack(pady=5)
        ttk.Button(control_frame, text="负片效果", command=self.negative_image).pack(pady=5)
        
    def create_menu(self):
        menu_bar = tk.Menu(self.root)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="打开", command=self.open_image)
        file_menu.add_command(label="保存", command=self.save_image)
        menu_bar.add_cascade(label="文件", menu=file_menu)
        self.root.config(menu=menu_bar)
    
    def open_image(self):
        path = filedialog.askopenfilename()
        if path:
            self.original_image = Image.open(path)
            self.processed_image = self.original_image.copy()
            self.display_images()
    
    def save_image(self):
        if self.processed_image:
            path = filedialog.asksaveasfilename(defaultextension=".png")
            if path:
                self.processed_image.save(path)
    
    def display_images(self):
        # 显示原图
        original = self.original_image.copy()
        w, h = original.size
        self.display_ratio = min(600/w, 600/h)
        original = original.resize((int(w*self.display_ratio), int(h*self.display_ratio)))
        self.original_photo = ImageTk.PhotoImage(original)
        self.original_canvas.create_image(0, 0, anchor=tk.NW, image=self.original_photo)
        
        # 显示处理结果
        processed = self.processed_image.copy()
        processed = processed.resize((int(w*self.display_ratio), int(h*self.display_ratio)))
        self.processed_photo = ImageTk.PhotoImage(processed)
        self.processed_canvas.create_image(0, 0, anchor=tk.NW, image=self.processed_photo)
    
    # 图像处理函数 ============================================
    
    def convert_grayscale(self):
        if self.processed_image:
            img = np.array(self.processed_image)
            if len(img.shape) == 3:
                gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
                self.processed_image = Image.fromarray(gray)
                self.display_images()
    
    def adjust_brightness_contrast(self):
        if self.processed_image:
            # 弹出调整对话框
            dialog = tk.Toplevel()
            dialog.title("亮度/对比度调整")
            
            alpha = tk.DoubleVar(value=1.0)
            beta = tk.DoubleVar(value=0.0)
            
            ttk.Label(dialog, text="对比度").pack()
            ttk.Scale(dialog, variable=alpha, from_=0.1, to=3.0).pack()
            
            ttk.Label(dialog, text="亮度").pack()
            ttk.Scale(dialog, variable=beta, from_=-100, to=100).pack()
            
            def apply_changes():
                img = np.array(self.processed_image, dtype=np.float32)
                img = alpha.get() * img + beta.get()
                img = np.clip(img, 0, 255).astype(np.uint8)
                self.processed_image = Image.fromarray(img)
                self.display_images()
                dialog.destroy()
            
            ttk.Button(dialog, text="应用", command=apply_changes).pack()
    
    def gamma_correction(self):
        if self.processed_image:
            dialog = tk.Toplevel()
            dialog.title("伽马校正")
            
            gamma = tk.DoubleVar(value=1.0)
            ttk.Scale(dialog, variable=gamma, from_=0.1, to=3.0).pack()
            
            def apply_gamma():
                img = np.array(self.processed_image, dtype=np.float32) / 255.0
                img = np.power(img, gamma.get())
                img = (img * 255).astype(np.uint8)
                self.processed_image = Image.fromarray(img)
                self.display_images()
                dialog.destroy()
            
            ttk.Button(dialog, text="应用", command=apply_gamma).pack()
    
    def flip_image(self, horizontal=True):
        if self.processed_image:
            if horizontal:
                self.processed_image = ImageOps.mirror(self.processed_image)
            else:
                self.processed_image = ImageOps.flip(self.processed_image)
            self.display_images()
    
    def gaussian_blur(self):
        if self.processed_image:
            dialog = tk.Toplevel()
            dialog.title("高斯模糊")
            
            sigma = tk.DoubleVar(value=1.0)
            ttk.Scale(dialog, variable=sigma, from_=0.1, to=10.0).pack()
            
            def apply_blur():
                img = np.array(self.processed_image)
                blurred = cv2.GaussianBlur(img, (0,0), sigma.get())
                self.processed_image = Image.fromarray(blurred)
                self.display_images()
                dialog.destroy()
            
            ttk.Button(dialog, text="应用", command=apply_blur).pack()
    
    def edge_detection(self):
        if self.processed_image:
            img = np.array(self.processed_image.convert('L'))
            dx = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=3)
            dy = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=3)
            edges = np.sqrt(dx**2 + dy**2)
            edges = (edges / edges.max() * 255).astype(np.uint8)
            self.processed_image = Image.fromarray(edges)
            self.display_images()
    
    def negative_image(self):
        if self.processed_image:
            self.processed_image = ImageOps.invert(self.processed_image)
            self.display_images()

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageProcessorApp(root)
    root.mainloop()
