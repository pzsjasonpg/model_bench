"""请求 vLLM 部署的 Embedding 模型示例"""

import requests


def get_embedding(text: str, model_name: str = "Qwen3-VL-Embedding-8B", url: str = "http://192.168.0.126:31001/v1/embeddings") -> list:
    """获取文本的 embedding 向量"""
    payload = {
        "input": text,
        "model": model_name,  # vLLM 通常不需要特定 model 名称，可留默认
    }
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    data = resp.json()
    return data["data"][0]["embedding"]


if __name__ == "__main__":
    texts = [
        "深度学习是机器学习的一个分支",
        "Transformer 架构在 NLP 领域取得了巨大成功",
    ]

    for t in texts:
        emb = get_embedding(t)
        print(f"文本: {t}")
        print(f"维度: {len(emb)}")
        print(f"前 10 维: {emb[:10]}")
        print("-" * 60)
