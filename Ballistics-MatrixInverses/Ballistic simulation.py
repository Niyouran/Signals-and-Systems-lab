import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.font_manager as fm
from typing import List, Dict, Tuple, Optional

# ========================
# 跨平台中文字体配置（优化异常处理）
# ========================
def configure_chinese_font() -> None:
    """自动检测并设置中文字体，添加异常处理"""
    try:
        system_fonts = fm.findSystemFonts()
        font_candidates = [
            'Microsoft YaHei', 'SimHei', 'Noto Sans CJK SC',
            'Arial Unicode MS', 'WenQuanYi Micro Hei', 'Sarasa UI SC'
        ]
        selected_font = next(
            (font for font in font_candidates
             if any(font.lower() in f.lower() for f in system_fonts)),
            None
        )
        if selected_font:
            plt.rcParams['font.sans-serif'] = [selected_font]
        else:
            messagebox.showwarning("字体警告", "未找到中文字体，将使用默认字体")
        plt.rcParams['axes.unicode_minus'] = False
    except Exception as e:
        messagebox.showerror("字体错误", f"字体配置失败: {str(e)}")

configure_chinese_font()

# ========================
# 弹道模拟核心类（添加类型提示和文档字符串）
# ========================
class BallisticSimulator:
    def __init__(self):
        self.simulations: List[Dict] = []
        self.color_cycle = plt.rcParams['axes.prop_cycle'].by_key()['color']

    @staticmethod
    def polar_to_vector(speed: float, angle_deg: float) -> Tuple[float, float]:
        """将极坐标转换为笛卡尔坐标向量"""
        theta = np.radians(angle_deg)
        return (speed * np.cos(theta), speed * np.sin(theta))

    def compute_dynamics(self, params: Dict) -> Tuple[np.ndarray, np.ndarray]:
        """
        计算动力学矩阵和偏移向量。
        h: 步长, m: 质量, eta: 阻力系数, w: 风速向量, g: 重力加速度向量
        """
        h = params['h']
        m = params['m']
        eta = params['eta']
        w = np.array(params['w'])
        g = np.array(params['g'])

        I = np.eye(2)
        hI = h * I
        drag_factor = 1 - (h * eta) / m

        A = np.block([
            [I, hI],
            [np.zeros((2, 2)), drag_factor * I]
        ])
        b = np.concatenate([
            np.zeros(2),
            h * (g + (eta / m) * w)
        ])
        return A, b

    def simulate(self, params: Dict) -> np.ndarray:
        """模拟弹道轨迹（向量化计算提升性能）"""
        A, b = self.compute_dynamics(params)
        x = np.concatenate([params['p0'], params['v0']])
        trajectory = np.zeros((params['T'] + 1, 2))
        trajectory[0] = params['p0']

        for t in range(1, params['T'] + 1):
            x = A @ x + b
            trajectory[t] = x[:2]
        return trajectory

    def calculate_optimal_v0(self, params: Dict, target: Tuple[float, float]) -> Tuple[float, float]:
        """计算目标追踪所需的最优初始速度（PDF第15页公式）"""
        A, b = self.compute_dynamics(params)
        T = params['T']
        F = np.linalg.matrix_power(A, T)
        j = sum(np.linalg.matrix_power(A, k) @ b for k in range(T))
        # 提取F12子矩阵和d向量
        C = F[:2, 2:]
        d = F[:2, :2] @ np.array(params['p0']) + j[:2]
        try:
            v0 = np.linalg.inv(C) @ (np.array(target) - d)
            return tuple(v0)
        except np.linalg.LinAlgError:
            raise ValueError("无法求解，目标位置不可达或参数不兼容")

    def add_simulation(self, params: Dict) -> None:
        """添加一次模拟参数到列表中"""
        self.simulations.append(params)

    def clear_simulations(self) -> None:
        """清除所有已添加的模拟参数"""
        self.simulations.clear()


# ========================
# 图形界面类（添加目标追踪及导出功能）
# ========================
class BallisticGUI:
    def __init__(self, master: tk.Tk):
        self.master = master
        self.simulator = BallisticSimulator()
        self.setup_ui()

    def setup_ui(self) -> None:
        """初始化用户界面（优化布局和交互）"""
        self.master.title("高级弹道模拟器 v2.0")
        self.master.geometry("1400x900")

        # 控制面板布局
        control_frame = ttk.Frame(self.master, width=350)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        # 绘图区域
        self.figure, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.master)
        self.canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 参数输入组件
        self.create_parameter_inputs(control_frame)
        self.create_target_inputs(control_frame)
        self.create_control_buttons(control_frame)

    def create_parameter_inputs(self, parent: ttk.Frame, min_val=None, max_val=None) -> None:
        """创建参数输入组件（优化验证逻辑）"""
        groups = [
            ("初始条件", [
                ("p0_x", "起始位置 X", 0.0),
                ("p0_y", "起始位置 Y", 0.0),
                ("v0_speed", "初速度大小", 50.0, (0, 500)),
                ("v0_angle", "发射仰角", 45.0, (0, 90))
            ]),
            ("环境参数", [
                ("w_x", "风速 X", -10.0),
                ("w_y", "风速 Y", 0.0),
                ("eta", "阻力系数", 0.05, (0, 1)),
                ("m", "质量", 5.0, (0.1, 100))
            ]),
            ("模拟参数", [
                ("T", "时间步数", 100, (1, 1000)),
                ("h", "步长", 0.1, (0.001, 1))
            ])
        ]

        self.entries = {}
        for group_name, params in groups:
            frame = ttk.LabelFrame(parent, text=group_name)
            frame.pack(fill=tk.X, pady=5)
            for i, (key, label, default, *validation) in enumerate(params):
                ttk.Label(frame, text=label).grid(row=i, column=0, sticky=tk.W)
                entry = ttk.Entry(frame)
                entry.insert(0, str(default))
                # 添加输入验证
                if validation:
                    min_val, max_val = validation[0]
                    v_func = (self.master.register(
                        lambda val, min_val=min_val, max_val=max_val:
                        self.validate_number(val, min_val, max_val)), '%P')
                    entry.config(validate="key", validatecommand=v_func)
                entry.grid(row=i, column=1, pady=2)
                self.entries[key] = entry

    def create_target_inputs(self, parent: ttk.Frame) -> None:
        """创建目标位置输入组件"""
        frame = ttk.LabelFrame(parent, text="目标追踪")
        frame.pack(fill=tk.X, pady=5)

        ttk.Label(frame, text="目标位置 X").grid(row=0, column=0)
        self.target_x = ttk.Entry(frame)
        self.target_x.grid(row=0, column=1)

        ttk.Label(frame, text="目标位置 Y").grid(row=1, column=0)
        self.target_y = ttk.Entry(frame)
        self.target_y.grid(row=1, column=1)

        ttk.Button(frame, text="计算最优初速", command=self.calculate_optimal_v0).grid(row=2, columnspan=2, pady=5)

    def create_control_buttons(self, parent: ttk.Frame) -> None:
        """创建控制按钮组"""
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(pady=15)

        buttons = [
            ("添加轨迹", self.add_trajectory),
            ("清除所有", self.clear_all),
            ("运行模拟", self.plot_trajectories),
            ("导出参数", self.export_parameters)
        ]
        for i, (text, command) in enumerate(buttons):
            ttk.Button(btn_frame, text=text, command=command).grid(row=0, column=i, padx=5)

    def validate_number(self, value: str, min_val: float, max_val: float) -> bool:
        """验证数值输入范围，同时允许空字符串"""
        if value == "":
            return True
        try:
            num = float(value)
            return min_val <= num <= max_val
        except ValueError:
            return False

    def get_params(self) -> Optional[Dict]:
        """获取并验证参数（增强错误处理）"""
        try:
            # 检查必填项是否为空
            for key in self.entries:
                if self.entries[key].get().strip() == "":
                    raise ValueError(f"参数 {key} 不能为空")
            params = {
                'p0': (
                    float(self.entries['p0_x'].get()),
                    float(self.entries['p0_y'].get())
                ),
                'v0': self.simulator.polar_to_vector(
                    float(self.entries['v0_speed'].get()),
                    float(self.entries['v0_angle'].get())
                ),
                'w': (
                    float(self.entries['w_x'].get()),
                    float(self.entries['w_y'].get())
                ),
                'eta': float(self.entries['eta'].get()),
                'm': float(self.entries['m'].get()),
                'T': int(self.entries['T'].get()),
                'h': float(self.entries['h'].get()),
                'g': (0, -9.8)
            }
            if params['m'] <= 0:
                raise ValueError("质量必须大于0")
            if params['h'] <= 0:
                raise ValueError("步长必须大于0")
            return params
        except ValueError as e:
            messagebox.showerror("输入错误", f"参数错误: {str(e)}")
            return None

    def calculate_optimal_v0(self) -> None:
        """计算并设置最优初始速度"""
        params = self.get_params()
        if not params:
            return
        try:
            if self.target_x.get().strip() == "" or self.target_y.get().strip() == "":
                raise ValueError("目标位置不能为空")
            target = (
                float(self.target_x.get()),
                float(self.target_y.get())
            )
            v0_opt = self.simulator.calculate_optimal_v0(params, target)
            speed = np.linalg.norm(v0_opt)
            angle = np.degrees(np.arctan2(v0_opt[1], v0_opt[0]))
            # 更新初速度输入框
            self.entries['v0_speed'].delete(0, tk.END)
            self.entries['v0_speed'].insert(0, f"{speed:.2f}")
            self.entries['v0_angle'].delete(0, tk.END)
            self.entries['v0_angle'].insert(0, f"{angle:.2f}")
            messagebox.showinfo("计算结果",
                                f"最优初速度:\nX: {v0_opt[0]:.2f} m/s\nY: {v0_opt[1]:.2f} m/s\n"
                                f"速度大小: {speed:.2f} m/s\n发射角: {angle:.2f}°")
            # 自动添加最优轨迹
            self.add_trajectory()
        except Exception as e:
            messagebox.showerror("计算错误", str(e))

    def add_trajectory(self) -> None:
        """添加轨迹（同时添加轨迹标签）"""
        params = self.get_params()
        if params:
            params['label'] = f"v0=({params['v0'][0]:.1f}, {params['v0'][1]:.1f})"
            self.simulator.add_simulation(params)

    def plot_trajectories(self) -> None:
        """绘制所有已添加的轨迹并添加标注信息"""
        self.ax.clear()
        for i, params in enumerate(self.simulator.simulations):
            try:
                traj = self.simulator.simulate(params)
                color = self.simulator.color_cycle[i % len(self.simulator.color_cycle)]
                label = params.get('label', f"轨迹 {i + 1}")
                # 绘制轨迹
                self.ax.plot(traj[:, 0], traj[:, 1], color=color, linewidth=2, label=label)
                # 标注落点
                end_point = traj[-1]
                self.ax.scatter(*end_point, color=color, zorder=5)
                self.ax.annotate(f"({end_point[0]:.1f}, {end_point[1]:.1f})",
                                 xy=end_point, xytext=(5, 5), textcoords='offset points',
                                 color=color)
                # 绘制最大高度线
                max_height = traj[:, 1].max()
                self.ax.axhline(max_height, color=color, linestyle='--', alpha=0.5)
            except Exception as e:
                messagebox.showerror("模拟错误", str(e))
                continue
        self.ax.set_xlabel("水平位置 (m)")
        self.ax.set_ylabel("垂直高度 (m)")
        self.ax.set_title("弹道轨迹模拟")
        self.ax.legend(loc='upper right')
        self.ax.grid(True, alpha=0.3)
        self.ax.axis('equal')
        self.canvas.draw()

    def clear_all(self) -> None:
        """清除所有模拟和绘图"""
        self.simulator.clear_simulations()
        self.ax.clear()
        self.canvas.draw()

    def export_parameters(self) -> None:
        """导出所有模拟参数到 JSON 文件"""
        if not self.simulator.simulations:
            messagebox.showwarning("导出警告", "当前没有可导出的参数")
            return
        try:
            # 弹出文件保存对话框
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON 文件", "*.json")],
                title="保存参数文件"
            )
            if file_path:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(self.simulator.simulations, f, ensure_ascii=False, indent=4)
                messagebox.showinfo("导出成功", f"参数已成功导出到 {file_path}")
        except Exception as e:
            messagebox.showerror("导出错误", f"参数导出失败: {str(e)}")

# ========================
# 运行程序
# ========================
if __name__ == "__main__":
    root = tk.Tk()
    app = BallisticGUI(root)
    root.mainloop()
