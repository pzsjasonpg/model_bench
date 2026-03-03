from huggingface_hub import snapshot_download

# 下载SynthData/Improved_Chinese_to_English数据集到data/translate目录
dataset_name = "SynthData/Improved_Chinese_to_English"
save_dir = "./data/translate"

print(f"开始下载 {dataset_name} 数据集到 {save_dir}...")
dataset_path = snapshot_download(
    dataset_name,
    cache_dir=save_dir,
    repo_type="dataset"
)

print(f"数据集下载完成，保存路径: {dataset_path}")
print("下载成功！")