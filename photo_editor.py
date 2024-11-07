import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk, ImageEnhance
from photo_configs import PhotoConfig
import math
from PIL import ImageDraw
from tkinter import messagebox

class PrintLayout:
    def __init__(self, paper_size, photo_size):
        # 特殊处理美国护照照片在4x6照相纸上的布局
        is_us_passport = (photo_size["width_mm"] == 51 and photo_size["height_mm"] == 51)  # 2x2 inch
        is_4x6_paper = (paper_size["width_mm"] == 152.4 and paper_size["height_mm"] == 101.6)  # 4x6 inch
        
        if is_us_passport and is_4x6_paper:
            # 使用实际英寸计算（忽略毫米的精确转换）
            self.rows = 2  # 4 inch 高度可以放 2 张 2x2 的照片
            self.cols = 3  # 6 inch 宽度可以放 3 张 2x2 的照片
            self.max_photos = self.rows * self.cols  # 最多 6 张
            
            # 计算每张照片的实际尺寸（稍微减小以确保打印效果）
            self.photo_width = 50.8  # 约 1.97 inch
            self.photo_height = 50.8
            
            # 计算边距使照片均匀分布
            self.actual_margin_x = (paper_size["width_mm"] - (self.cols * self.photo_width)) / 2
            self.actual_margin_y = (paper_size["height_mm"] - (self.rows * self.photo_height)) / 2
        else:
            # 其他照片类型使用原始的精确计算
            self.paper_width = paper_size["width_mm"]
            self.paper_height = paper_size["height_mm"]
            self.photo_width = photo_size["width_mm"]
            self.photo_height = photo_size["height_mm"]
            
            # 设置2mm边距
            self.margin_mm = 0
            self.spacing_mm = 0
            
            # 计算可用空间
            self.usable_width = self.paper_width - 2 * self.margin_mm
            self.usable_height = self.paper_height - 2 * self.margin_mm
            
            # 计算常规布局
            self.calculate_layout()
    
    def calculate_layout(self):
        """计算最大可打印数量和最优布局"""
        # 计算每个方向可以放置的最大数量（无间距）
        cols = int(self.usable_width / self.photo_width)
        rows = int(self.usable_height / self.photo_height)
        
        self.max_photos = rows * cols
        self.rows = rows
        self.cols = cols
        
        # 计算实际边距以使布局居中
        self.actual_margin_x = (self.paper_width - (cols * self.photo_width)) / 2
        self.actual_margin_y = (self.paper_height - (rows * self.photo_height)) / 2
    
    def get_photo_positions(self, num_photos):
        """获取照片位置"""
        positions = []
        for i in range(min(num_photos, self.max_photos)):
            row = i // self.cols
            col = i % self.cols
            
            if hasattr(self, 'actual_margin_x'):
                # 美国护照照片的特殊布局
                x = self.actual_margin_x + col * self.photo_width
                y = self.actual_margin_y + row * self.photo_height
            else:
                # 常规布局
                x = self.margin_mm + col * self.photo_width
                y = self.margin_mm + row * self.photo_height
            
            positions.append((x, y))
        
        return positions

class PrintPreviewWindow:
    def __init__(self, parent, cropped_photo, paper_size, num_photos, id_photo_spec):
        self.preview_window = tk.Toplevel(parent)
        self.preview_window.title("Print Preview")
        
        # 保存原始的裁剪后照片（PIL Image格式）
        self.original_photo = cropped_photo  # PIL Image
        self.paper_size = paper_size
        self.num_photos = num_photos
        self.id_photo_spec = id_photo_spec
        
        # 计算预览画布大小（等比例缩小）
        scale = 0.5  # 预览窗口缩放比例
        self.canvas_width = int(paper_size["width_mm"] * paper_size["dpi"] / 25.4 * scale)
        self.canvas_height = int(paper_size["height_mm"] * paper_size["dpi"] / 25.4 * scale)
        
        # 创建预览画布
        self.canvas = tk.Canvas(self.preview_window, 
                              width=self.canvas_width,
                              height=self.canvas_height,
                              bg='white')
        self.canvas.pack(pady=10)
        
        # 添加按钮
        button_frame = tk.Frame(self.preview_window)
        button_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Button(button_frame, text="Save", 
                 command=self.save_print_layout).pack(side='left', padx=5)
        tk.Button(button_frame, text="Cancel",
                 command=self.preview_window.destroy).pack(side='left', padx=5)
        
        # 创建布局计算器
        self.layout = PrintLayout(paper_size, id_photo_spec)
        
        # 显示预览
        self.create_preview()
        
    def create_preview(self):
        # 清除画布
        self.canvas.delete("all")
        
        # 计算预览缩放比例
        scale = self.canvas_width / self.paper_size["width_mm"]
        
        # 获取照片位置
        positions = self.layout.get_photo_positions(self.num_photos)
        
        # 计算预览中照片的尺寸
        preview_photo_width = round(self.id_photo_spec["width_mm"] * scale)
        preview_photo_height = round(self.id_photo_spec["height_mm"] * scale)
        
        # 在画布上显示所有位置
        for i, (x, y) in enumerate(positions):
            preview_x = round(x * scale)
            preview_y = round(y * scale)
            
            # 如果这个位置需要显示照片
            if i < self.num_photos:
                # 先用PIL Image调整大小
                preview_size = (preview_photo_width, preview_photo_height)
                resized_photo = self.original_photo.resize(preview_size, Image.Resampling.LANCZOS)
                
                # 然后转换为PhotoImage
                if not hasattr(self, 'preview_images'):
                    self.preview_images = []
                self.preview_images.append(ImageTk.PhotoImage(resized_photo))
                
                # 显示照片
                self.canvas.create_image(
                    preview_x, preview_y,
                    image=self.preview_images[-1],
                    anchor='nw'
                )
                
                # 在照片上绘制黑色细实线边框
                self.canvas.create_rectangle(
                    preview_x, preview_y,
                    preview_x + preview_photo_width,
                    preview_y + preview_photo_height,
                    outline='black',
                    width=1  # 设置线条宽度为1像素
                )
        
    def save_print_layout(self):
        # 创建实际尺寸的打印图像（使用实际DPI）
        paper_width_px = int(self.paper_size["width_mm"] * self.paper_size["dpi"] / 25.4)
        paper_height_px = int(self.paper_size["height_mm"] * self.paper_size["dpi"] / 25.4)
        
        # 创建白色背景的图像
        print_image = Image.new('RGB', 
                              (paper_width_px, paper_height_px),
                              'white')
        
        # 计算实际照片尺寸（像素）
        photo_width_px = int(self.id_photo_spec["width_mm"] * self.paper_size["dpi"] / 25.4)
        photo_height_px = int(self.id_photo_spec["height_mm"] * self.paper_size["dpi"] / 25.4)
        
        # 获取照片位置（毫米）
        positions = self.layout.get_photo_positions(self.num_photos)
        
        # 创建绘图对象用于画边框
        draw = ImageDraw.Draw(print_image)
        
        # 在每个位置粘贴照片并画边框
        for i, (x_mm, y_mm) in enumerate(positions):
            if i < self.num_photos:
                # 转换位置为像素
                x_px = int(x_mm * self.paper_size["dpi"] / 25.4)
                y_px = int(y_mm * self.paper_size["dpi"] / 25.4)
                
                # 调整原始照片到正确尺寸
                photo_resized = self.original_photo.resize(
                    (photo_width_px, photo_height_px),
                    Image.Resampling.LANCZOS
                )
                
                # 粘贴照片
                print_image.paste(photo_resized, (x_px, y_px))
                
                # 画黑色边框
                draw.rectangle(
                    [x_px, y_px, 
                     x_px + photo_width_px - 1,  # -1 避免边框重叠
                     y_px + photo_height_px - 1],
                    outline='black',
                    width=1
                )
        
        # 保存图像
        save_path = filedialog.asksaveasfilename(
            defaultextension=".jpg",
            filetypes=[("JPEG files", "*.jpg")],
            initialfile="print_layout.jpg"
        )
        
        if save_path:
            # 保存高质量图片
            print_image.save(save_path, "JPEG", quality=95, dpi=(300, 300))
            messagebox.showinfo("Success", "Print layout saved successfully!")
            self.preview_window.destroy()  # 关闭预览窗口

class PhotoEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("ID Photo Editor")
        
        # Initialize photo configuration
        self.photo_config = PhotoConfig()
        self.current_spec = None
        
        # Initialize variables
        self.canvas_width = 800
        self.canvas_height = 1000
        self.image = None
        self.image_on_canvas = None
        self.image_offset_x = self.canvas_width // 2
        self.image_offset_y = self.canvas_height // 2
        self.scale = 1.0
        self.start_x = self.start_y = 0
        self.brightness = 1.0
        self.contrast = 1.0
        
        # 添加调整模式变量
        self.adjustment_mode = tk.StringVar()
        self.adjustment_mode.set("Manual Adjustment")  # 默认为手动模式
        
        # 添加模式切换按钮
        self.add_mode_switch()
        
        # Setup UI components
        self.create_canvas()
        self.setup_ui()
        self.add_adjustment_controls()
        
        # Add status label
        self.status_label = tk.Label(root, text="请上传图片", fg="black")
        self.status_label.pack(side="bottom", pady=5)
        
        # Add keyboard shortcuts
        self.root.bind('<Control-o>', lambda e: self.upload_image())
        self.root.bind('<Control-s>', lambda e: self.save_cropped_image())
        
        # 设置默认为美国护照
        self.type_var.set("US Passport")
        self.update_photo_spec()  # 立即更新裁剪框和辅助线
        
        # 添加打印按钮
        self.add_print_controls()

    def create_canvas(self):
        # Create canvas
        self.canvas = tk.Canvas(self.root, width=self.canvas_width, 
                              height=self.canvas_height, bg='grey')
        self.canvas.pack(pady=10)
        
        # Bind events
        self.canvas.bind("<B1-Motion>", self.move_image)
        self.canvas.bind("<ButtonPress-1>", self.start_move)
        self.canvas.bind("<MouseWheel>", self.zoom_image)

    def setup_ui(self):
        # Create control frame
        control_frame = tk.Frame(self.root)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        # Document type selection
        type_frame = tk.Frame(control_frame)
        type_frame.pack(fill='x', pady=5)
        
        tk.Label(type_frame, text="Document Type:").pack(side='left')
        self.type_var = tk.StringVar()
        type_combo = ttk.Combobox(type_frame, 
                                 textvariable=self.type_var,
                                 values=list(PhotoConfig.SPECIFICATIONS.keys()),
                                 state='readonly')
        type_combo.pack(side='left', padx=5)
        type_combo.set("P.R.China Passport")  # Default selection
        type_combo.bind('<<ComboboxSelected>>', self.update_photo_spec)
        
        # Buttons
        button_frame = tk.Frame(control_frame)
        button_frame.pack(fill='x', pady=5)
        
        tk.Button(button_frame, text="Upload Image", command=self.upload_image).pack(side="left", padx=5)
        tk.Button(button_frame, text="Save Photo", command=self.save_cropped_image).pack(side="left", padx=5)
        
        # Initialize photo specifications
        self.update_photo_spec()

    def update_photo_spec(self, event=None):
        # Get selected document type specifications
        spec = PhotoConfig.SPECIFICATIONS[self.type_var.get()]
        self.current_spec = spec
        
        # Calculate crop box dimensions (mm to pixels)
        self.target_width_px = int(spec["width_mm"] * spec["dpi"] / 25.4)
        self.target_height_px = int(spec["height_mm"] * spec["dpi"] / 25.4)
        
        # Set minimum recommended resolution
        self.min_width = self.target_width_px * 2
        self.min_height = self.target_height_px * 2
        
        # Update crop box
        self.draw_crop_box()

    def upload_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg;*.jpeg;*.png")])
        if not file_path:
            return

        # Open original image
        original = Image.open(file_path)
        
        # Create white background
        white_bg = Image.new("RGB", original.size, (255, 255, 255))
        
        # Handle transparent background
        if original.mode in ('RGBA', 'LA') or (original.mode == 'P' and 'transparency' in original.info):
            white_bg.paste(original, (0, 0), original)
            self.original_image = white_bg
        else:
            self.original_image = original.convert("RGB")

        # Check image resolution
        if self.original_image.size[0] < self.min_width or self.original_image.size[1] < self.min_height:
            self.status_label.config(
                text=f"Warning: Recommended resolution is at least {self.min_width}x{self.min_height} pixels",
                fg="red"
            )
        else:
            self.status_label.config(text="Image loaded successfully", fg="green")

        self.image = self.original_image.copy()
        
        # Reset scale and position
        self.scale = 1.0
        self.image_offset_x = self.canvas_width // 2
        self.image_offset_y = self.canvas_height // 2
        self.show_image()

    def show_image(self):
        if self.image:
            # Resize image based on scale
            w, h = self.image.size
            resized_image = self.image.resize(
                (int(w * self.scale), int(h * self.scale)), 
                Image.Resampling.LANCZOS
            )

            # Convert to Tkinter image
            self.tk_image = ImageTk.PhotoImage(resized_image)

            # Update canvas
            if self.image_on_canvas:
                self.canvas.delete(self.image_on_canvas)
            self.image_on_canvas = self.canvas.create_image(
                self.image_offset_x, 
                self.image_offset_y, 
                anchor='center', 
                image=self.tk_image
            )

            # Update crop box
            self.draw_crop_box()

            # 在显示图片后重绘辅助线
            self.draw_guide_lines()

    def draw_crop_box(self):
        # Remove old mask and box
        self.canvas.delete("crop_box")
        
        # Calculate crop box position
        x1 = (self.canvas_width - self.target_width_px) // 2
        y1 = (self.canvas_height - self.target_height_px) // 2
        x2 = x1 + self.target_width_px
        y2 = y1 + self.target_height_px
        
        # Draw dark overlay
        self.canvas.create_rectangle(0, 0, self.canvas_width, y1, 
                                   fill="black", stipple="gray25", tags="crop_box")
        self.canvas.create_rectangle(0, y2, self.canvas_width, self.canvas_height, 
                                   fill="black", stipple="gray25", tags="crop_box")
        self.canvas.create_rectangle(0, y1, x1, y2, 
                                   fill="black", stipple="gray25", tags="crop_box")
        self.canvas.create_rectangle(x2, y1, self.canvas_width, y2, 
                                   fill="black", stipple="gray25", tags="crop_box")
        
        # Draw crop box border
        self.canvas.create_rectangle(x1, y1, x2, y2, 
                                   outline="white", width=2, tags="crop_box")

        # 在绘制完裁剪框后添加辅助线
        self.draw_guide_lines()

    def start_move(self, event):
        # Record initial mouse position
        self.start_x, self.start_y = event.x, event.y

    def move_image(self, event):
        # Adjust image position based on mouse movement
        dx = event.x - self.start_x
        dy = event.y - self.start_y
        self.image_offset_x += dx
        self.image_offset_y += dy
        self.start_x, self.start_y = event.x, event.y
        self.show_image()

    def zoom_image(self, event):
        # Control zoom scale
        zoom_factor = 1.1 if event.delta > 0 else 0.9
        self.scale *= zoom_factor
        self.show_image()

    def save_cropped_image(self):
        if not self.image:
            self.status_label.config(text="Please upload an image first", fg="red")
            return

        # 获取调整后的图片
        w, h = self.original_image.size
        
        # 先应用亮度和对比度调整
        adjusted_image = self.original_image.copy()
        enhancer = ImageEnhance.Brightness(adjusted_image)
        adjusted_image = enhancer.enhance(self.brightness)
        enhancer = ImageEnhance.Contrast(adjusted_image)
        adjusted_image = enhancer.enhance(self.contrast)
        
        # 进行缩放
        resized_image = adjusted_image.resize(
            (int(w * self.scale), int(h * self.scale)), 
            Image.Resampling.LANCZOS
        )

        # 创建白色背景图片
        final_image = Image.new(
            "RGB", 
            (self.target_width_px, self.target_height_px), 
            self.current_spec["bg_color"]
        )

        # 计算裁剪位置
        crop_x1 = (self.canvas_width - self.target_width_px) / 2
        crop_y1 = (self.canvas_height - self.target_height_px) / 2
        
        # 向上取整以避免缝隙
        crop_x2 = math.ceil(crop_x1 + self.target_width_px)
        crop_y2 = math.ceil(crop_y1 + self.target_height_px)

        # 转换为图片坐标
        x1 = int((crop_x1 - (self.image_offset_x - resized_image.width / 2)))
        y1 = int((crop_y1 - (self.image_offset_y - resized_image.height / 2)))
        x2 = int((crop_x2 - (self.image_offset_x - resized_image.width / 2)))
        y2 = int((crop_y2 - (self.image_offset_y - resized_image.height / 2)))

        # 计算实际粘贴区域，使用 math.ceil 确保没有缝隙
        paste_x = int(max(0, -x1))
        paste_y = int(max(0, -y1))
        crop_x = int(max(0, x1))
        crop_y = int(max(0, y1))
        crop_right = math.ceil(min(resized_image.width, x2))
        crop_bottom = math.ceil(min(resized_image.height, y2))

        # 如果有可见的图像区域
        if crop_right > crop_x and crop_bottom > crop_y:
            # 裁剪可见部分
            cropped = resized_image.crop((crop_x, crop_y, crop_right, crop_bottom))
            # 粘贴到白色背景上
            final_image.paste(cropped, (paste_x, paste_y))

        # 保存图片
        save_path = filedialog.asksaveasfilename(
            defaultextension=".jpg",
            filetypes=[("JPEG files", "*.jpg")]
        )
        if save_path:
            final_image.save(save_path, quality=95)
            self.status_label.config(text="Photo saved successfully", fg="green")

    def add_adjustment_controls(self):
        # Create adjustment frame
        adjust_frame = tk.Frame(self.root)
        adjust_frame.pack(fill='x', padx=10, pady=5)
        
        # Brightness control
        tk.Label(adjust_frame, text="Brightness:").pack(side='left')
        self.brightness_scale = tk.Scale(
            adjust_frame, 
            from_=0.8,
            to=1.2,
            resolution=0.05,
            orient='horizontal', 
            command=self.update_adjustments,
            length=200
        )
        self.brightness_scale.set(1.0)
        self.brightness_scale.pack(side='left', padx=5)
        
        # Contrast control
        tk.Label(adjust_frame, text="Contrast:").pack(side='left')
        self.contrast_scale = tk.Scale(
            adjust_frame, 
            from_=0.8,
            to=1.2,
            resolution=0.05,
            orient='horizontal', 
            command=self.update_adjustments,
            length=200
        )
        self.contrast_scale.set(1.0)
        self.contrast_scale.pack(side='left', padx=5)

    def update_adjustments(self, event=None):
        if hasattr(self, 'original_image'):
            # Get current adjustment values
            self.brightness = self.brightness_scale.get()
            self.contrast = self.contrast_scale.get()
            
            # Apply adjustments
            img = self.original_image.copy()
            
            # Apply brightness
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(self.brightness)
            
            # Apply contrast
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(self.contrast)
            
            self.image = img
            self.show_image()

    def add_mode_switch(self):
        # 创建模式切换框架
        mode_frame = tk.Frame(self.root)
        mode_frame.pack(fill='x', padx=10, pady=5)
        
        # 添加单选按钮
        tk.Radiobutton(mode_frame, 
                      text="Manual Adjustment",
                      variable=self.adjustment_mode,
                      value="Manual Adjustment",
                      command=self.update_guide_lines).pack(side='left', padx=10)
                      
        tk.Radiobutton(mode_frame, 
                      text="Auto Adjustment",
                      variable=self.adjustment_mode,
                      value="Auto Adjustment",
                      command=self.update_guide_lines).pack(side='left', padx=10)

    def draw_guide_lines(self):
        # 删除现有的辅助线
        self.canvas.delete("guide_lines")
        
        if self.adjustment_mode.get() == "Manual Adjustment" and self.current_spec:
            # 获取裁剪框的位置
            x1 = (self.canvas_width - self.target_width_px) // 2
            y1 = (self.canvas_height - self.target_height_px) // 2
            x2 = x1 + self.target_width_px
            y2 = y1 + self.target_height_px
            
            # 绘制垂直居中线
            dash_pattern = (5, 5)  # 5像素线段，5像素空格
            center_x = (x1 + x2) // 2
            self.canvas.create_line(center_x, y1, center_x, y2,
                                  dash=dash_pattern, fill='white',
                                  tags="guide_lines")
            
            # 计算毫米到像素的换比例
            mm_to_px = self.current_spec["dpi"] / 25.4
            
            # 绘制眼睛位置范围线（两条绿线）
            eyes_min_y = y2 - int(self.current_spec["guide_lines"]["eyes_position_min"] * mm_to_px)
            eyes_max_y = y2 - int(self.current_spec["guide_lines"]["eyes_position_max"] * mm_to_px)
            
            self.canvas.create_line(x1, eyes_min_y, x2, eyes_min_y,
                                  dash=dash_pattern, fill='green',
                                  tags="guide_lines")
            self.canvas.create_line(x1, eyes_max_y, x2, eyes_max_y,
                                  dash=dash_pattern, fill='green',
                                  tags="guide_lines")
            
            # 以眼睛位置的中点为基准，绘制头部尺寸范围线
            eyes_center_y = (eyes_min_y + eyes_max_y) / 2
            head_min = self.current_spec["guide_lines"]["head_size_min"] * mm_to_px
            head_max = self.current_spec["guide_lines"]["head_size_max"] * mm_to_px
            
            # 绘制头部范围的四条线（黄线）
            # 最小头部尺寸的上下线（内侧两条线）
            head_top_min = eyes_center_y - int(head_min * 0.4)  # 头顶位置（较小范围）
            head_bottom_min = eyes_center_y + int(head_min * 0.6)  # 下巴位置（较小范围）
            
            # 最大头部尺寸的上下线（外侧两条线）
            head_top_max = eyes_center_y - int(head_max * 0.4)  # 头顶位置（较大范围）
            head_bottom_max = eyes_center_y + int(head_max * 0.6)  # 下巴位置（较大范围）
            
            # 绘制所有头部范围线
            for y in [head_top_max, head_top_min, head_bottom_min, head_bottom_max]:
                self.canvas.create_line(x1, y, x2, y,
                                      dash=dash_pattern, fill='yellow',
                                      tags="guide_lines")

    def update_guide_lines(self):
        # 更新辅助线显示
        self.draw_guide_lines()

    def add_print_controls(self):
        print_frame = tk.Frame(self.root)
        print_frame.pack(fill='x', padx=10, pady=5)
        
        # 照片纸尺寸选择
        tk.Label(print_frame, text="Paper Size:").pack(side='left')
        self.paper_size_var = tk.StringVar()
        paper_combo = ttk.Combobox(print_frame,
                                 textvariable=self.paper_size_var,
                                 values=list(PhotoConfig.PAPER_SIZES.keys()),
                                 state='readonly')
        paper_combo.set("4x6 inch")
        paper_combo.pack(side='left', padx=5)
        
        # 照片数量选择
        tk.Label(print_frame, text="Number of Photos:").pack(side='left')
        self.num_photos_var = tk.StringVar()
        num_combo = ttk.Combobox(print_frame,
                               textvariable=self.num_photos_var,
                               values=["2", "4", "6", "8", "12"],
                               state='readonly')
        num_combo.set("4")
        num_combo.pack(side='left', padx=5)
        
        # 打印预览按钮
        tk.Button(print_frame, text="Print Preview",
                 command=self.show_print_preview).pack(side='left', padx=5)
        
    def show_print_preview(self):
        if not self.image:
            self.status_label.config(text="Please upload an image first", fg="red")
            return
            
        # 获取裁剪后的照片（保持为PIL Image格式）
        cropped_photo = self.get_cropped_photo()
        if cropped_photo:
            paper_size = PhotoConfig.PAPER_SIZES[self.paper_size_var.get()]
            num_photos = int(self.num_photos_var.get())
            
            preview = PrintPreviewWindow(
                self.root, 
                cropped_photo,  # PIL Image 格式
                paper_size, 
                num_photos,
                self.current_spec
            )
    
    def get_cropped_photo(self):
        """获取裁剪后的照片，返回PIL Image对象"""
        if not self.image:
            return None

        # 获取调整后的图片
        w, h = self.original_image.size
        
        # 应用亮度和对比度调整
        adjusted_image = self.original_image.copy()
        enhancer = ImageEnhance.Brightness(adjusted_image)
        adjusted_image = enhancer.enhance(self.brightness)
        enhancer = ImageEnhance.Contrast(adjusted_image)
        adjusted_image = enhancer.enhance(self.contrast)
        
        # 进行缩放
        resized_image = adjusted_image.resize(
            (int(w * self.scale), int(h * self.scale)), 
            Image.Resampling.LANCZOS
        )

        # 创建白色背景图片
        final_image = Image.new(
            "RGB", 
            (self.target_width_px, self.target_height_px), 
            self.current_spec["bg_color"]
        )

        # 计算裁剪位置
        crop_x1 = (self.canvas_width - self.target_width_px) / 2
        crop_y1 = (self.canvas_height - self.target_height_px) / 2
        
        # 计算实际裁剪区域
        x1 = int((crop_x1 - (self.image_offset_x - resized_image.width / 2)))
        y1 = int((crop_y1 - (self.image_offset_y - resized_image.height / 2)))
        x2 = int(x1 + self.target_width_px)
        y2 = int(y1 + self.target_height_px)

        # 计算粘贴位置
        paste_x = max(0, -x1)
        paste_y = max(0, -y1)
        crop_x = max(0, x1)
        crop_y = max(0, y1)
        crop_right = min(resized_image.width, x2)
        crop_bottom = min(resized_image.height, y2)

        if crop_right > crop_x and crop_bottom > crop_y:
            cropped = resized_image.crop((crop_x, crop_y, crop_right, crop_bottom))
            final_image.paste(cropped, (paste_x, paste_y))
            
            return final_image  # 直接返回PIL Image对象，不转换为PhotoImage
        return None


# Create and run application
if __name__ == "__main__":
    root = tk.Tk()
    app = PhotoEditor(root)
    root.mainloop()