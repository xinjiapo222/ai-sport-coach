# AI Sport Coach

面向家庭训练和体育体测的边缘智能运动教练。系统通过摄像头或示例视频识别人体姿态，支持俯卧撑、深蹲、跳绳、仰卧起坐和引体向上五类项目，提供自动计数、动作反馈、骨架显示和实时波形。

## 主要特性

- MoveNet SinglePose Lightning：输出 17 个人体关键点。
- 稀疏光流跟踪：减少推理间隔内的骨架滞后。
- 可解释状态机：基于关节角度、相对位置和位移完成计数。
- PySide6 中文界面：支持项目切换、参数设置和实时曲线。
- 双平台后端：普通 PC 使用 MediaPipe，RISC-V K1 使用 ONNX Runtime。
- 全离线运行：视频无需上传云端。

## 目录结构

```text
ai-sport-coach/
├── assets/videos/       # 五类示例视频
├── core/                # 姿态检测与几何计算
├── exercises/           # 各运动项目状态机
├── models/              # MoveNet ONNX 模型
├── ui/                  # PySide6 界面与视频线程
├── utils/               # 配置、中文绘制与语音工具
├── main.py              # 程序入口
├── requirements.txt     # PC 端依赖
├── requirements-k1.txt  # Bianbu/K1 系统包清单
└── run-k1.sh            # K1 启动脚本
```

## PC 运行

建议使用 Python 3.10。

```bash
python -m venv .venv

# Linux/macOS
source .venv/bin/activate

# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
python main.py
```

## K1 Pro / Bianbu 运行

使用 Bianbu 软件源安装 `requirements-k1.txt` 中列出的系统包，然后执行：

```bash
chmod +x run-k1.sh
./run-k1.sh
```

默认摄像头设备编号为 `20`。如需修改：

```bash
AI_SPORT_CAMERA=0 ./run-k1.sh
```

## 使用说明

1. 保证人物全身进入画面，避免强逆光和多人重叠。
2. 在左侧选择运动项目及摄像头或示例视频。
3. 根据需要在设置界面调整动作阈值、分辨率和音量。
4. 计数、动作反馈和波形会在训练过程中实时更新。

## 第三方模型

仓库内的 MoveNet SinglePose Lightning 模型源自 Google MoveNet，并采用 ONNX 格式用于端侧推理。使用或再分发时请同时遵守相应模型及依赖组件的许可证。
