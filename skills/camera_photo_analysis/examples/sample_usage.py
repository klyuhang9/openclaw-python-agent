"""
使用示例：拍摄并分析人像照片

运行方式：
    python sample_usage.py
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from camera_photo_analysis import capture_photo, analyze_photo


def main():
    """主函数：演示完整的拍摄和分析流程"""
    
    print("=" * 60)
    print("📸 摄像头拍摄与人像分析技能演示")
    print("=" * 60)
    print()
    
    # 步骤 1: 拍摄照片
    print("步骤 1: 拍摄照片...")
    print("-" * 60)
    capture_result = capture_photo(
        output_path="~/Desktop/my_photo.png",
        wait_time=2
    )
    
    if not capture_result["success"]:
        print(f"❌ {capture_result['message']}")
        return
    
    print(f"✅ {capture_result['message']}")
    print()
    
    # 步骤 2: 分析照片
    print("步骤 2: 分析照片...")
    print("-" * 60)
    analysis_result = analyze_photo(
        image_path=capture_result["path"],
        prompt=None  # 使用默认提示词
    )
    
    if not analysis_result["success"]:
        print(f"❌ {analysis_result['message']}")
        return
    
    # 打印分析结果
    print()
    print("=" * 60)
    print("📊 qwen3-397b 人像分析报告")
    print("=" * 60)
    print()
    print(analysis_result["analysis"])
    print()
    print("=" * 60)
    print("✅ 分析完成")
    print("=" * 60)


def analyze_existing_photo(photo_path: str):
    """
    分析已有照片
    
    Args:
        photo_path: 照片路径
    """
    print(f"分析已有照片：{photo_path}")
    print("-" * 60)
    
    result = analyze_photo(image_path=photo_path)
    
    if result["success"]:
        print("\n" + "=" * 60)
        print("📊 分析结果")
        print("=" * 60)
        print(result["analysis"])
        print("=" * 60)
    else:
        print(f"❌ {result['message']}")


if __name__ == "__main__":
    # 运行完整演示
    main()
    
    # 或者分析已有照片（取消注释使用）
    # analyze_existing_photo("~/Desktop/team_photo.png")
