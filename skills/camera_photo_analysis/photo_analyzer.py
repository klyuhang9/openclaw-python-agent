"""
照片分析模块
使用 qwen3-397b 多模态模型分析人像照片
"""

import base64
import requests
import json
from typing import Optional


class PhotoAnalyzer:
    """照片分析器"""
    
    def __init__(
        self,
        base_url: str = "http://10.72.0.44:8001/v1",
        api_key: str = "VLLM_API_KEY",
        model: str = "qwen3-397b"
    ):
        """
        初始化分析器
        
        Args:
            base_url: API 基础 URL
            api_key: API 密钥
            model: 模型名称
        """
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def _image_to_base64(self, image_path: str) -> str:
        """
        将图片转换为 base64 编码
        
        Args:
            image_path: 图片路径
            
        Returns:
            str: base64 编码的字符串
        """
        with open(image_path, 'rb') as f:
            image_data = f.read()
            return base64.b64encode(image_data).decode('utf-8')
    
    def analyze(
        self,
        image_path: str,
        prompt: Optional[str] = None
    ) -> dict:
        """
        分析照片
        
        Args:
            image_path: 照片路径
            prompt: 自定义分析提示词（可选）
            
        Returns:
            dict: {
                "success": bool,
                "analysis": str,
                "message": str
            }
        """
        # 默认提示词
        if prompt is None:
            prompt = """请详细分析这张照片中的人物，告诉我：

1. **基本描述**：照片中的人物有什么外貌特征？（性别、大致年龄、发型、面部特征等）
2. **表情和情绪**：人物的表情如何？传达出什么样的情绪或状态？
3. **穿着打扮**：人物穿着什么衣服？有什么配饰？整体风格如何？
4. **环境背景**：照片的背景是什么？在什么场景下拍摄的？
5. **光线和构图**：照片的光线如何？构图有什么特点？
6. **其他观察**：还有什么值得注意的细节？

请用中文回答，描述要友好、尊重且详细。"""
        
        try:
            # 转换为 base64
            image_base64 = self._image_to_base64(image_path)
            
            # 构建请求
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 4096,
                "temperature": 0.7
            }
            
            # 发送请求
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis = result['choices'][0]['message']['content']
                
                return {
                    "success": True,
                    "analysis": analysis,
                    "message": "✅ 分析完成"
                }
            else:
                return {
                    "success": False,
                    "analysis": None,
                    "message": f"❌ API 错误：{response.status_code} - {response.text}"
                }
                
        except FileNotFoundError:
            return {
                "success": False,
                "analysis": None,
                "message": f"❌ 文件不存在：{image_path}"
            }
        except Exception as e:
            return {
                "success": False,
                "analysis": None,
                "message": f"❌ 分析异常：{str(e)}"
            }


def analyze_photo(
    image_path: str,
    prompt: Optional[str] = None,
    base_url: str = "http://10.72.0.44:8001/v1",
    api_key: str = "VLLM_API_KEY",
    model: str = "qwen3-397b"
) -> dict:
    """
    便捷函数：分析照片
    
    Args:
        image_path: 照片路径
        prompt: 自定义提示词（可选）
        base_url: API 基础 URL
        api_key: API 密钥
        model: 模型名称
        
    Returns:
        dict: 分析结果
    """
    analyzer = PhotoAnalyzer(base_url=base_url, api_key=api_key, model=model)
    return analyzer.analyze(image_path, prompt)


if __name__ == "__main__":
    # 测试分析
    print("测试照片分析功能...")
    result = analyze_photo("/Users/klyuhang9/Desktop/my_photo.png")
    
    if result["success"]:
        print("\n" + "=" * 60)
        print("📸 分析结果")
        print("=" * 60)
        print(result["analysis"])
        print("=" * 60)
    else:
        print(result["message"])
