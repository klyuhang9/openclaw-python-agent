---
description: 创建并运行定时天气监控任务（后台进程）
---

# 天气监控任务技能

## 📋 技能说明

本技能用于创建、运行和管理定时天气监控后台任务。使用 Python 的 `schedule` 库实现定时查询，通过 `nohup` 在系统后台长期运行。

## 🎯 适用场景

- 需要定期查询天气信息
- 需要任务在后台持续运行（关闭终端后继续）
- 需要记录历史查询日志

## 📝 完整流程

### 1️⃣ 创建天气监控脚本

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
北京天气定时查询任务
每分钟查询一次北京当前天气
"""

import schedule
import time
import requests
import sys
from datetime import datetime

# 禁用输出缓冲
sys.stdout.reconfigure(line_buffering=True)

# 使用 Open-Meteo 免费天气 API（无需 API key）
# 北京坐标：纬度 39.9042, 经度 116.4074
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"

def get_beijing_weather():
    """查询北京当前天气"""
    try:
        params = {
            "latitude": 39.9042,
            "longitude": 116.4074,
            "current": [
                "temperature_2m",
                "relative_humidity_2m",
                "weather_code",
                "wind_speed_10m",
                "wind_direction_10m"
            ],
            "timezone": "Asia/Shanghai"
        }
        
        response = requests.get(WEATHER_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        current = data.get("current", {})
        
        # 天气代码解读
        weather_codes = {
            0: "晴朗", 1: "主要晴朗", 2: "部分多云", 3: "多云",
            45: "雾", 48: "雾凇",
            51: "毛毛雨", 53: "中度毛毛雨", 55: "密集毛毛雨",
            61: "小雨", 63: "中雨", 65: "大雨",
            71: "小雪", 73: "中雪", 75: "大雪",
            80: "小阵雨", 81: "中阵雨", 82: "大阵雨",
            95: "雷雨", 96: "雷阵雨伴冰雹", 99: "雷阵雨伴大冰雹"
        }
        
        weather_code = current.get("weather_code", 0)
        weather_desc = weather_codes.get(weather_code, "未知")
        
        # 格式化输出
        print("=" * 50, flush=True)
        print(f"📍 北京天气查询", flush=True)
        print(f"⏰ 查询时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
        print(f"🌡️  温度：{current.get('temperature_2m', 'N/A')}°C", flush=True)
        print(f"💧 湿度：{current.get('relative_humidity_2m', 'N/A')}%", flush=True)
        print(f"🌤️  天气：{weather_desc}", flush=True)
        print(f"💨 风速：{current.get('wind_speed_10m', 'N/A')} km/h", flush=True)
        print(f"🧭 风向：{current.get('wind_direction_10m', 'N/A')}°", flush=True)
        print("=" * 50, flush=True)
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 天气查询失败：{e}", flush=True)
    except Exception as e:
        print(f"❌ 发生错误：{e}", flush=True)

def main():
    """主函数"""
    print("🚀 北京天气监控任务已启动", flush=True)
    print(f"⏰ 启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print()
    
    # 立即执行一次
    get_beijing_weather()
    
    # 设置定时任务：每分钟执行
    schedule.every(1).minutes.do(get_beijing_weather)
    
    # 保持运行
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
```

### 2️⃣ 启动后台任务

```bash
# 启动任务（后台运行 + 日志记录）
nohup python3 ~/beijing_weather_monitor.py > ~/weather_monitor.log 2>&1 &

# 获取进程 ID
echo $!
# 或
ps aux | grep beijing_weather_monitor.py | grep -v grep
```

### 3️⃣ 查看运行状态

```bash
# 查看进程是否运行
ps aux | grep beijing_weather_monitor.py | grep -v grep

# 查看实时日志
tail -f ~/weather_monitor.log

# 查看最新 10 条记录
tail -10 ~/weather_monitor.log

# 查看全部日志
cat ~/weather_monitor.log
```

### 4️⃣ 停止任务

```bash
# 方法 1：使用进程 ID（推荐）
kill <PID>

# 方法 2：一键停止
pkill -f "beijing_weather_monitor.py"

# 方法 3：强制停止（如果无法正常停止）
kill -9 <PID>
```

## 🔧 自定义配置

### 修改查询频率

编辑脚本中的：
```python
schedule.every(1).minutes.do(get_beijing_weather)  # 每分钟
# 改为：
schedule.every(5).minutes.do(get_beijing_weather)  # 每 5 分钟
schedule.every(1).hours.do(get_beijing_weather)    # 每小时
```

### 修改查询城市

编辑脚本中的坐标：
```python
params = {
    "latitude": 39.9042,  # 北京纬度
    "longitude": 116.4074,  # 北京经度
    ...
}
```

常用城市坐标：
- 上海：31.2304, 121.4737
- 广州：23.1291, 113.2644
- 深圳：22.5431, 114.0579

### 修改日志文件位置

```bash
nohup python3 ~/beijing_weather_monitor.py > /path/to/your/logfile.log 2>&1 &
```

## ⚠️ 注意事项

1. **输出缓冲**：脚本中使用了 `sys.stdout.reconfigure(line_buffering=True)` 和 `flush=True` 确保实时输出

2. **API 限制**：Open-Meteo 是免费 API，无需 API key，但有速率限制

3. **进程持久化**：使用 `nohup` 确保关闭终端后任务继续运行

4. **日志管理**：定期清理日志文件避免占用过多磁盘空间
   ```bash
   # 清空日志文件
   > ~/weather_monitor.log
   ```

5. **依赖安装**：
   ```bash
   pip install schedule requests
   ```

## 🐛 常见问题

| 问题 | 解决方案 |
|------|---------|
| 日志没有实时更新 | 确保脚本中有 `flush=True` |
| 进程自动退出 | 检查网络连接和 API 可用性 |
| 无法停止进程 | 使用 `kill -9 <PID>` 强制停止 |
| 日志文件过大 | 定期清空或轮转日志 |

## 📋 快速命令参考

```bash
# 启动
nohup python3 ~/beijing_weather_monitor.py > ~/weather_monitor.log 2>&1 &

# 查看进程
ps aux | grep beijing_weather_monitor.py | grep -v grep

# 查看日志
tail -f ~/weather_monitor.log

# 停止
pkill -f "beijing_weather_monitor.py"
```
