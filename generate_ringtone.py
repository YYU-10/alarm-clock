"""生成默认铃声WAV文件"""
import struct
import wave
import os
import math


def generate_beep(filepath: str, freq=880, duration=2.0, sample_rate=44100):
    """生成简单正弦波蜂鸣音"""
    n_samples = int(sample_rate * duration)
    samples = []
    for i in range(n_samples):
        t = i / sample_rate
        # 使用带衰减的正弦波，模拟铃声节奏
        envelope = 1.0 if (t % 0.5) < 0.3 else 0.0
        value = math.sin(2 * math.pi * freq * t) * envelope * 0.7
        samples.append(int(value * 32767))

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with wave.open(filepath, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))


if __name__ == "__main__":
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ringtones", "default.wav")
    generate_beep(out_path)
    print(f"已生成默认铃声: {out_path}")
