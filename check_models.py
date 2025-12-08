#!/usr/bin/env python3
"""
检查可用的模型列表
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv(".mcp_env")

# 获取环境变量
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

if not api_key:
    print("❌ 错误: 未找到 OPENAI_API_KEY 环境变量")
    exit(1)

print(f"🔍 正在查询可用模型...")
print(f"📍 API Base URL: {base_url}")
print()

# 调用 /v1/models 接口
url = f"{base_url.rstrip('/')}/v1/models"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

try:
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    
    if "data" in data:
        models = data["data"]
        print(f"✅ 找到 {len(models)} 个可用模型:\n")
        
        # 按模型 ID 排序并显示
        model_ids = sorted([model.get("id", "unknown") for model in models])
        
        for i, model_id in enumerate(model_ids, 1):
            print(f"  {i:3d}. {model_id}")
        
        # 检查是否有 gpt-5 相关模型
        print("\n" + "="*60)
        gpt5_models = [m for m in model_ids if "gpt-5" in m.lower()]
        if gpt5_models:
            print(f"✅ 找到 GPT-5 相关模型: {', '.join(gpt5_models)}")
        else:
            print("❌ 未找到 gpt-5.1 或其他 GPT-5 相关模型")
            print("💡 建议使用以下模型:")
            gpt4_models = [m for m in model_ids if "gpt-4" in m.lower()]
            if gpt4_models:
                for model in gpt4_models[:5]:  # 显示前5个 GPT-4 模型
                    print(f"   - {model}")
    else:
        print("❌ 响应格式不符合预期:")
        print(data)
        
except requests.exceptions.RequestException as e:
    print(f"❌ 请求失败: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"状态码: {e.response.status_code}")
        print(f"响应内容: {e.response.text}")

