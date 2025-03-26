import os
import math
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
from ttkbootstrap import Style
from pydub import AudioSegment
from pydub.effects import speedup
from moviepy.editor import *
from moviepy.video.fx.all import *


class MediaProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Media Processor Pro")
        self.style = Style(theme="flatly")
        self.setup_ui()

    def setup_ui(self):
        # 媒体类型选择
        self.media_type = tk.StringVar(value="audio")
        ttk.Label(self.root, text="媒体类型:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Radiobutton(self.root, text="音频", variable=self.media_type, value="audio").grid(row=0, column=1,
                                                                                              sticky="w")
        ttk.Radiobutton(self.root, text="视频", variable=self.media_type, value="video").grid(row=0, column=2,
                                                                                              sticky="w")

        # 文件路径选择
        ttk.Label(self.root, text="文件路径:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.path_entry = ttk.Entry(self.root, width=40)
        self.path_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(self.root, text="浏览", command=self.browse_file).grid(row=1, column=2, padx=5, pady=5)

        # 操作选择
        ttk.Label(self.root, text="操作类型:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.operation = tk.StringVar()
        self.operation_combo = ttk.Combobox(
            self.root,
            textvariable=self.operation,
            values=[
                "加速/减速", "倒放", "延迟",
                "回声效果", "音量调整",
                "绿幕抠像", "动态文字", "高级滤镜"
            ]
        )
        self.operation_combo.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.operation_combo.bind("<<ComboboxSelected>>", self.show_parameters)

        # 参数输入区域
        self.param_frame = ttk.Frame(self.root)
        self.param_frame.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

        # 处理按钮
        ttk.Button(self.root, text="开始处理", command=self.process_media).grid(row=4, column=1, pady=10)

        # 进度条
        self.progress = ttk.Progressbar(self.root, mode='determinate')
        self.progress.grid(row=5, column=0, columnspan=3, sticky="ew", padx=10)

    def browse_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, file_path)

    def show_parameters(self, event=None):
        for widget in self.param_frame.winfo_children():
            widget.destroy()

        operation = self.operation.get()
        if operation == "加速/减速":
            ttk.Label(self.param_frame, text="速度倍数:").grid(row=0, column=0, padx=5)
            self.speed_factor = ttk.Entry(self.param_frame)
            self.speed_factor.grid(row=0, column=1, padx=5)
        elif operation == "延迟":
            ttk.Label(self.param_frame, text="延迟时间(秒):").grid(row=0, column=0, padx=5)
            self.delay_time = ttk.Entry(self.param_frame)
            self.delay_time.grid(row=0, column=1, padx=5)
        elif operation == "回声效果":
            ttk.Label(self.param_frame, text="延迟时间(秒):").grid(row=0, column=0, padx=5)
            self.echo_delay = ttk.Entry(self.param_frame)
            self.echo_delay.grid(row=0, column=1, padx=5)
            ttk.Label(self.param_frame, text="衰减系数(0-1):").grid(row=1, column=0, padx=5)
            self.echo_decay = ttk.Entry(self.param_frame)
            self.echo_decay.grid(row=1, column=1, padx=5)
        elif operation == "音量调整":
            ttk.Label(self.param_frame, text="增益分贝(例 +3 或 -5):").grid(row=0, column=0, padx=5)
            self.gain_db = ttk.Entry(self.param_frame)
            self.gain_db.grid(row=0, column=1, padx=5)
        elif operation == "绿幕抠像":
            ttk.Label(self.param_frame, text="背景色(R,G,B):").grid(row=0, column=0)
            self.chroma_color = ttk.Entry(self.param_frame, text="0,255,0")
            self.chroma_color.grid(row=0, column=1)
            ttk.Label(self.param_frame, text="色差容差(1-100):").grid(row=1, column=0)
            self.chroma_threshold = ttk.Scale(self.param_frame, from_=1, to=100, orient="horizontal")
            self.chroma_threshold.set(30)
            self.chroma_threshold.grid(row=1, column=1)
        elif operation == "动态文字":
            ttk.Label(self.param_frame, text="文字内容:").grid(row=0, column=0)
            self.text_content = ttk.Entry(self.param_frame)
            self.text_content.grid(row=0, column=1)
            ttk.Label(self.param_frame, text="起始时间(秒):").grid(row=1, column=0)
            self.text_start = ttk.Entry(self.param_frame)
            self.text_start.grid(row=1, column=1)
            ttk.Label(self.param_frame, text="持续时间(秒):").grid(row=2, column=0)
            self.text_duration = ttk.Entry(self.param_frame)
            self.text_duration.grid(row=2, column=1)
        elif operation == "高级滤镜":
            ttk.Label(self.param_frame, text="滤镜类型:").grid(row=0, column=0)
            self.filter_type = ttk.Combobox(self.param_frame,
                                            values=["赛博朋克", "老电影", "漫画风格"]
                                            )
            self.filter_type.grid(row=0, column=1)

    def process_media(self):
        media_type = self.media_type.get()
        input_path = self.path_entry.get()
        operation = self.operation.get()

        if not os.path.exists(input_path):
            messagebox.showerror("错误", "文件路径不存在！")
            return

        self.progress["value"] = 0
        self.root.update_idletasks()

        try:
            if media_type == "audio":
                self.process_audio(input_path, operation)
            else:
                self.process_video(input_path, operation)

            self.progress["value"] = 100
            messagebox.showinfo("成功", "处理完成！输出文件与源文件同目录")
        except Exception as e:
            messagebox.showerror("错误", f"处理失败: {str(e)}")
        finally:
            self.progress["value"] = 0

    # ====== 音频处理 ======
    def process_audio(self, input_path, operation):
        audio = AudioSegment.from_file(input_path)
        base, ext = os.path.splitext(input_path)

        if operation == "加速/减速":
            speed = float(self.speed_factor.get())
            output = self.speed_processing(audio, speed)
        elif operation == "倒放":
            output = audio.reverse()
        elif operation == "延迟":
            delay_time = float(self.delay_time.get()) * 1000
            silence = AudioSegment.silent(duration=delay_time)
            output = silence + audio
        elif operation == "回声效果":
            delay_time = float(self.echo_delay.get())
            decay_coeff = float(self.echo_decay.get())
            output = self.apply_echo(audio, delay_time, decay_coeff)
        elif operation == "音量调整":
            gain_db = float(self.gain_db.get())
            output = audio.apply_gain(gain_db)
        else:
            raise ValueError("未知操作")

        output_path = f"{base}_processed{ext}"
        output.export(output_path, format=ext[1:])
        self.progress["value"] = 80

    def speed_processing(self, audio, speed):
        if speed <= 0:
            raise ValueError("速度倍数必须大于0")
        return speedup(audio, speed, 150) if speed > 1 else audio._spawn(
            audio.raw_data,
            overrides={"frame_rate": int(audio.frame_rate * speed)}
        ).set_frame_rate(audio.frame_rate)

    def apply_echo(self, audio, delay_seconds, decay_coeff):
        if decay_coeff <= 0 or decay_coeff > 1:
            raise ValueError("衰减系数必须在0到1之间")

        delay_ms = int(delay_seconds * 1000)
        decay_db = 20 * math.log10(decay_coeff)

        silence = AudioSegment.silent(duration=delay_ms)
        original_length = len(audio)
        decayed_audio = audio.apply_gain(decay_db)
        echo_segment = silence + decayed_audio

        echo_segment = (echo_segment * (original_length // len(echo_segment) + 1))[:original_length]
        return audio.overlay(echo_segment)

    # ====== 视频处理 ======
    def process_video(self, input_path, operation):
        video = VideoFileClip(input_path)
        base, ext = os.path.splitext(input_path)
        processed = None

        if operation == "加速/减速":
            speed = float(self.speed_factor.get())
            processed = video.fx(vfx.speedx, speed)
        elif operation == "倒放":
            processed = video.fx(vfx.time_mirror)
        elif operation == "延迟":
            delay = float(self.delay_time.get())
            processed = concatenate_videoclips([ColorClip(video.size, (0, 0, 0), duration=delay), video])
        elif operation == "绿幕抠像":
            rgb = tuple(map(int, self.chroma_color.get().split(',')))
            threshold = self.chroma_threshold.get() / 100
            processed = self.apply_chroma_key(video, rgb, threshold)
        elif operation == "动态文字":
            text = self.text_content.get()
            start_time = float(self.text_start.get())
            duration = float(self.text_duration.get())
            processed = self.add_animated_text(video, text, start_time, duration)
        elif operation == "高级滤镜":
            filter_name = self.filter_type.get()
            processed = self.apply_adv_filter(video, filter_name)
        else:
            raise ValueError("未知操作")

        output_path = f"{base}_processed.mp4"
        processed.write_videofile(output_path, codec="libx264", audio_codec="aac")

    def apply_chroma_key(self, clip, rgb_color, threshold):
        target_color = np.array(rgb_color) / 255.0

        def mask_frame(frame):
            distance = np.sqrt(np.sum((frame / 255.0 - target_color) ** 2, axis=2))
            mask = np.where(distance > threshold, 255, 0).astype("uint8")
            return mask

        mask_clip = clip.fl_image(lambda f: np.stack([mask_frame(f)] * 3, axis=2)).to_mask()
        return clip.set_mask(mask_clip)

    def add_animated_text(self, clip, text, start_time, duration):
        text_clip = TextClip(
            text, fontsize=40, color='yellow',
            font='Arial-Bold', stroke_color='black', stroke_width=1
        )
        text_clip = text_clip.set_start(start_time).set_duration(duration).crossfadein(0.5)
        return CompositeVideoClip([clip, text_clip.set_pos(('center', 'bottom'))])

    def apply_adv_filter(self, clip, filter_name):
        if filter_name == "赛博朋克":
            return clip.fx(vfx.colorx, 1.5).fx(vfx.contrast, 1.2)
        elif filter_name == "老电影":
            return clip.fx(vfx.time_symmetrize).fx(vfx.blackwhite).fx(vfx.gaussian_blur, 1)
        elif filter_name == "漫画风格":
            return clip.fl_image(lambda frame: (frame // 64) * 64)
        return clip


if __name__ == "__main__":
    root = tk.Tk()
    app = MediaProcessorApp(root)
    root.mainloop()
