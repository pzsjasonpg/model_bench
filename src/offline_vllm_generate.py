import numpy as np
from vllm import LLM, SamplingParams
import time
from transformers import AutoTokenizer

def get_tokenizer(model_path: str):
    """获取模型的分词器"""
    return AutoTokenizer.from_pretrained(model_path)



def generate_prompts(tokenizer: AutoTokenizer, num_prompts: int = 100, prompt_length: int = 100) -> list[str]:
    """生成随机提示"""
    prompts = []
    for _ in range(num_prompts):
        prompt = tokenizer.decode(np.random.randint(100, tokenizer.vocab_size - 100, size=prompt_length))
        prompts.append(prompt)
    return prompts
    


def main():
    # Create an LLM.
    model_path = "Qwen3/Qwen3-8B"
    # num_prompts = 1
    prompt_length = 100
    output_token_max_length = 100
    # Create a sampling params object.
    tokenizer = get_tokenizer(model_path)
    sampling_params = SamplingParams(temperature=0.8, top_p=0.95, ignore_eos=True, min_tokens=output_token_max_length, max_tokens=output_token_max_length)
    llm = LLM(model=model_path, tensor_parallel_size=1, gpu_memory_utilization=0.9, max_model_len=32768)


    batch_sizes = [1, 2, 4, 8, 16, 32, 64]
    for num_prompts in batch_sizes:
        # Generate texts from the prompts.
        prompts = generate_prompts(tokenizer, num_prompts=num_prompts, prompt_length=prompt_length)
        # The output is a list of RequestOutput objects
        # that contain the prompt, generated text, and other information.
        start_time = time.time() * 1000
        outputs = llm.generate(prompts, sampling_params)
        end_time = time.time() * 1000
        total_time = end_time - start_time
        #print(f"Total time: {total_time} ms")
        # Print the outputs.
        #print("\nGenerated Outputs:\n" + "-" * 60)
        #print(f"Total prompts: {len(prompts)}")
        #print(f"Total outputs: {len(outputs)}")
        output_num_tokens = 0
        for output in outputs:
            prompt = output.prompt
            generated_text = output.outputs[0].text
            #print(f"Prompt:    {prompt!r}")
            #print(f"Output:    {generated_text!r}")
            output_num_tokens += len(tokenizer(generated_text)["input_ids"])
        #print("-" * 60)
        #print(f"Total input tokens: {len(prompts)*prompt_length}")
        #print(f"Total output tokens: {output_num_tokens}")
        #print(f"Total input token throughput: {len(prompts)*prompt_length/total_time} tokens/ms")
        #print(f"Total output token throughput: {output_num_tokens/total_time} tokens/ms")
        #print(f"Total token throughput: {(output_num_tokens+len(prompts)*prompt_length)/total_time} tokens/prompt")

        

    


if __name__ == "__main__":
    main()