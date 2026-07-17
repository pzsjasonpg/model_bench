"""使用 OpenAI SDK 请求 Embedding 模型示例"""

from openai import OpenAI


def get_embedding(text: str) -> list:
    client = OpenAI(
        base_url="http://192.168.0.126:31001/v1",
        api_key="not-needed",  # vLLM 通常不校验 key，但字段需要占位
    )
    resp = client.embeddings.create(
        model="Qwen3-VL-Embedding-8B",
        input=text,
    )
    return resp.data[0].embedding


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
