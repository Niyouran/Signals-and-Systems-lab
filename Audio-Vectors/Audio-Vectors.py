import os
import math
import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ttkbootstrap import Style
from pydub import AudioSegment
from pydub.effects import speedup


class AudioProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("音频处理器 (向量化优化版)")
        self.style = Style(theme="flatly")
        self.setup_ui()

        # 初始化类型转换映射
        self.dtype_map = {
            1: np.int8,
            2: np.int16,
            4: np.int32
        }

    def setup_ui(self):
        # 文件路径选择
        ttk.Label(self.root, text="文件路径:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.path_entry = ttk.Entry(self.root, width=40)
        self.path_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(self.root, text="浏览", command=self.browse_file).grid(row=0, column=2, padx=5, pady=5)

        # 操作选择
        ttk.Label(self.root, text="操作类型:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.operation = tk.StringVar()
        self.operation_combo = ttk.Combobox(
            self.root,
            textvariable=self.operation,
            values=["加速/减速", "倒放", "延迟", "回声效果", "音量调整"]
        )
        self.operation_combo.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.operation_combo.bind("<<ComboboxSelected>>", self.show_parameters)

        # 参数输入区域
        self.param_frame = ttk.Frame(self.root)
        self.param_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

        # 处理按钮
        ttk.Button(self.root, text="开始处理", command=self.process_audio).grid(row=3, column=1, pady=10)

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("音频文件", "*.wav *.mp3 *.ogg")])
        if file_path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, file_path)

    def show_parameters(self, event=None):
        for widget in self.param_frame.winfo_children():
            widget.destroy()

        operation = self.operation.get()
        if operation == "加速/减速":
            ttk.Label(self.param_frame, text="速度倍数 (0.1-3.0):").grid(row=0, column=0, padx=5)
            self.speed_factor = ttk.Entry(self.param_frame)
            self.speed_factor.grid(row=0, column=1, padx=5)
        elif operation == "延迟":
            ttk.Label(self.param_frame, text="延迟时间(秒):").grid(row=0, column=0, padx=5)
            self.delay_time = ttk.Entry(self.param_frame)
            self.delay_time.grid(row=0, column=1, padx=5)
        elif operation == "回声效果":
            ttk.Label(self.param_frame, text="延迟时间(0.01-2秒):").grid(row=0, column=0, padx=5)
            self.echo_delay = ttk.Entry(self.param_frame)
            self.echo_delay.grid(row=0, column=1, padx=5)
            ttk.Label(self.param_frame, text="衰减系数(0.1-0.9):").grid(row=1, column=0, padx=5)
            self.echo_decay = ttk.Entry(self.param_frame)
            self.echo_decay.grid(row=1, column=1, padx=5)
        elif operation == "音量调整":
            ttk.Label(self.param_frame, text="增益分贝 (-20~+20):").grid(row=0, column=0, padx=5)
            self.gain_db = ttk.Entry(self.param_frame)
            self.gain_db.grid(row=0, column=1, padx=5)

    def process_audio(self):
        input_path = self.path_entry.get()
        operation = self.operation.get()

        if not os.path.exists(input_path):
            messagebox.showerror("错误", "文件路径不存在！")
            return

        try:
            audio = AudioSegment.from_file(input_path)
            if audio.sample_width not in [1, 2, 4]:
                raise ValueError("不支持的音频位深度")

            processed = self.apply_operation(audio, operation)
            self.save_output(processed, input_path)
            messagebox.showinfo("成功",
                                f"处理完成！\n处理前时长: {len(audio) / 1000:.1f}秒\n处理后时长: {len(processed) / 1000:.1f}秒")
        except Exception as e:
            messagebox.showerror("错误", f"处理失败: {str(e)}")

    def apply_operation(self, audio, operation):
        """应用选定的音频处理操作"""
        if operation == "加速/减速":
            return self.speed_processing(audio, float(self.speed_factor.get()))
        elif operation == "倒放":
            return self.reverse_processing(audio)
        elif operation == "延迟":
            return self.add_delay(audio, float(self.delay_time.get()))
        elif operation == "回声效果":
            return self.apply_echo(audio, float(self.echo_delay.get()), float(self.echo_decay.get()))
        elif operation == "音量调整":
            return self.gain_processing(audio, float(self.gain_db.get()))
        else:
            raise ValueError("未知操作")

    def audio_to_array(self, audio):
        """将AudioSegment转换为优化后的NumPy数组"""
        return np.frombuffer(audio.raw_data, dtype=self.dtype_map[audio.sample_width])

    def array_to_audio(self, array, audio):
        """将NumPy数组转换回AudioSegment"""
        return audio._spawn(array.tobytes())

    def speed_processing(self, audio, speed_factor):
        if speed_factor <= 0.1 or speed_factor > 3.0:
            raise ValueError("速度倍数必须在0.1到3.0之间")

        if speed_factor > 1:
            return speedup(audio, speed_factor, 150)
        else:
            orig_array = self.audio_to_array(audio)
            new_length = int(len(orig_array) / speed_factor)

            # 向量化插值处理
            indices = np.clip(
                np.arange(new_length) * speed_factor,
                0,
                len(orig_array) - 1
            ).astype(int)

            return self.array_to_audio(orig_array[indices], audio).set_frame_rate(
                int(audio.frame_rate * speed_factor)
            )

    def reverse_processing(self, audio):
        """向量化反转音频"""
        samples = self.audio_to_array(audio)
        return self.array_to_audio(samples[::-1], audio)

    def add_delay(self, audio, delay_seconds):
        """高效的延迟添加"""
        delay_ms = int(delay_seconds * 1000)
        silence = AudioSegment.silent(
            duration=delay_ms,
            frame_rate=audio.frame_rate
        )
        return silence + audio

    def apply_echo(self, audio, delay_seconds, decay_coeff):
        """向量化回声效果"""
        if not (0.1 <= decay_coeff <= 0.9):
            raise ValueError("衰减系数必须在0.1到0.9之间")

        # 转换为数组进行向量化操作
        samples = self.audio_to_array(audio).astype(np.float32)
        sample_rate = audio.frame_rate
        delay_samples = int(delay_seconds * sample_rate)

        # 创建衰减回声
        decayed = np.zeros_like(samples)
        start = min(delay_samples, len(samples))
        decayed[start:] = samples[:len(samples) - start] * decay_coeff

        # 混合原始信号和回声
        mixed = samples + decayed

        # 防止溢出
        max_val = np.iinfo(self.dtype_map[audio.sample_width]).max
        return self.array_to_audio(
            np.clip(mixed, -max_val, max_val).astype(self.dtype_map[audio.sample_width]),
            audio
        )

    def gain_processing(self, audio, gain_db):
        """向量化音量调整"""
        if not (-20 <= gain_db <= 20):
            raise ValueError("增益必须在-20到+20分贝之间")

        samples = self.audio_to_array(audio).astype(np.float32)
        ratio = 10 ** (gain_db / 20)

        # 向量化增益应用
        scaled = samples * ratio

        # 裁剪和类型转换
        max_val = np.iinfo(self.dtype_map[audio.sample_width]).max
        return self.array_to_audio(
            np.clip(scaled, -max_val, max_val).astype(self.dtype_map[audio.sample_width]),
            audio
        )

    def save_output(self, audio, original_path):
        """保存处理结果"""
        base, ext = os.path.splitext(original_path)
        output_path = f"{base}_processed{ext}"

        # 根据原始格式保存
        format = ext[1:] if ext[1:] in ['wav', 'ogg'] else 'mp3'
        audio.export(output_path, format=format)


if __name__ == "__main__":
    root = tk.Tk()
    app = AudioProcessorApp(root)
    root.mainloop()
