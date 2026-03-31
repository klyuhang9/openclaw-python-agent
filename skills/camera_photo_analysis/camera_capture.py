"""
摄像头拍摄模块
使用 imagesnap 工具拍摄照片
"""

import subprocess
import os
from pathlib import Path


def capture_photo(output_path: str = "~/Desktop/my_photo.png", wait_time: int = 2) -> dict:
    """
    使用 macOS 摄像头拍摄照片
    
    Args:
        output_path: 照片保存路径，默认 ~/Desktop/my_photo.png
        wait_time: 拍摄前等待时间（秒），默认 2 秒
    
    Returns:
        dict: {
            "success": bool,
            "path": str,
            "size": str,
            "message": str
        }
    """
    # 展开路径
    output_path = os.path.expanduser(output_path)
    
    try:
        # 检查 imagesnap 是否安装
        result = subprocess.run(
            ["which", "imagesnap"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return {
                "success": False,
                "path": None,
                "size": None,
                "message": "❌ imagesnap 未安装，请运行：brew install imagesnap"
            }
        
        # 拍摄照片
        print(f"📸 正在准备拍摄，{wait_time}秒后拍摄...")
        capture_cmd = f"imagesnap -w {wait_time} {output_path}"
        result = subprocess.run(
            capture_cmd,
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return {
                "success": False,
                "path": None,
                "size": None,
                "message": f"❌ 拍摄失败：{result.stderr}"
            }
        
        # 获取文件大小
        size_result = subprocess.run(
            ["ls", "-lh", output_path],
            capture_output=True,
            text=True
        )
        
        file_size = size_result.stdout.split()[4] if size_result.returncode == 0 else "Unknown"
        
        return {
            "success": True,
            "path": output_path,
            "size": file_size,
            "message": f"✅ 照片已保存到：{output_path} ({file_size})"
        }
        
    except Exception as e:
        return {
            "success": False,
            "path": None,
            "size": None,
            "message": f"❌ 拍摄异常：{str(e)}"
        }


def check_camera_permission() -> bool:
    """
    检查是否有摄像头访问权限
    
    Returns:
        bool: 是否有权限
    """
    try:
        # 尝试快速拍摄（不保存）
        result = subprocess.run(
            ["imagesnap", "-l"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


if __name__ == "__main__":
    # 测试拍摄
    print("测试摄像头拍摄功能...")
    result = capture_photo()
    print(result["message"])
