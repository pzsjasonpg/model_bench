# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project
# Adapted from
# https://github.com/vllm-project/vllm/blob/main/benchmarks/benchmark_long_document_qa_throughput.py

"""
Commandline arguments:
    --num-total-documents: The number of documents to sample prompts from.

    --document-length: The length of each document in tokens.
                       (Optional, default: 20000)

    --output-len: The number of tokens to generate for each prompt.
                  (Optional, default: 100)

    --num-requests: The number of requests to send.

    --num-docs-per-request: The number of documents to use in each prompt.

    --sampling-strategy: The sampling strategy to use. Currently only supports
                         "random".

    --random-seed: Random seed when the repeat mode is "random".
                    (Optional, default: 0)

    --blend-special-str: The special string to use for blending documents.
                         (Optional, default: " # # ")

    --port: Port to query the vLLM server

    --model: Model name

    --max-inflight-requests: Maximum number of in-flight requests. Default is 2

    --sleep-time-after-warmup: Sleep time after warm up iteration.
                              (Optional, default: 0.0 seconds)

    --output: Filename to write all responses to. If omitted, writes to stdout.

    --expected-ttft-gain: Expected minimum speed-up in time-to-first-token
                         (warmup/query) as a factor, e.g. 4.3 for 4.3×. If
                         actual gain is below this, exits.

    --expected-latency-gain: Expected minimum speed-up in total round time
                            (warmup/query) as a factor, e.g. 4.5 for 4.5×.
                            If actual gain is below this, exits.
"""

# Standard
import argparse
import asyncio
import random
import sys
import time

# Third Party
from openai import AsyncOpenAI
import pandas as pd
from transformers import AutoTokenizer

# Global output filename (set in __main__)
OUTPUT_FILE = None

from dataclasses import dataclass

@dataclass
class RequestStats:
    prompt_id: int
    request_start: float
    ttft: float
    request_end: float
    successful: bool
    prompt_tokens: int = 0
    completion_tokens: int = 0


def has_content(chunk):
    """
    Check if the chunk has content in the choices.
    Args:
        chunk: The response chunk from OpenAI API.

    Returns:
        bool: True if content exists, False otherwise.
    """
    return chunk.choices and chunk.choices[0].text


def extract_content(chunk):
    """
    Extract content from the response chunk.
    Args:
        chunk: The response chunk from OpenAI API.
    Returns:
        str: The content extracted from the chunk.
    """
    if chunk.choices[0].text is not None:
        return chunk.choices[0].text
    else:
        return ""


def write_resp(text: str):
    """
    Write text to the specified output file (if any), otherwise to stdout.
    """
    if OUTPUT_FILE:
        with open(OUTPUT_FILE, "a") as resp_file:
            resp_file.write(text)
    else:
        sys.stdout.write(text)


async def process_single_prompt(
    client, model, prompt, prompt_index, total_prompts, output_len, semaphore, tokenizer=None
):
    """
    Process a single prompt with the given client and model.

    Args:
        client: The OpenAI client for making API calls.
        model: The model name to use for generation.
        prompt: The prompt string to be processed.
        prompt_index: Index of the current prompt (0-based).
        total_prompts: Total number of prompts being processed.
        output_len: The maximum number of tokens to generate.
        semaphore: Asyncio semaphore to limit concurrent requests.
        tokenizer: Tokenizer for counting tokens.

    Returns:
        RequestStats: RequestStats object containing the request stats
    """
    async with semaphore:  # Acquire semaphore to limit concurrent requests
        write_resp(f"\n--- Sending prompt {prompt_index + 1}/{total_prompts} ---\n")
        start_time = time.time()
        first_token_time = None
        words = ""

        response = await client.completions.create(
            model=model,
            prompt=prompt,
            max_tokens=output_len,
            temperature=0.0,
            stream=True,
            extra_body={"ignore_eos": True},
        )

        responses = []
        usage = None
        # Collect the response chunks
        async for chunk in response:
            if not chunk.choices:
                continue

            # Handle content for chat completions
            if has_content(chunk):
                content = extract_content(chunk)
                if first_token_time is None and content != "":
                    first_token_time = time.time()
                responses.append(content)
                words += content
            
            # Check for usage information in the final chunk
            if hasattr(chunk, 'usage') and chunk.usage:
                usage = chunk.usage

        end_time = time.time()
        final_response = "".join(responses)
        write_resp(f"\nResponse of request {prompt_index}: {final_response}\n")

        # TTFT < 0 means not successful
        ttft = (first_token_time - start_time) if first_token_time is not None else -1
        
        # Calculate token usage
        prompt_tokens = 0
        completion_tokens = 0
        if usage:
            # 优先使用API返回的usage信息
            prompt_tokens = getattr(usage, 'prompt_tokens', 0)
            completion_tokens = getattr(usage, 'completion_tokens', 0)
        elif tokenizer:
            # Use tokenizer to count tokens if usage info is not available
            if isinstance(prompt, list):
                # If prompt is already token IDs, use its length
                prompt_tokens = len(prompt)
            else:
                # 计算prompt的token数
                try:
                    prompt_tokens = len(tokenizer.encode(prompt))
                except Exception as e:
                    # 如果tokenizer编码失败，使用简单的空格分割计数
                    prompt_tokens = len(prompt.split())
            # 计算response的token数
            try:
                completion_tokens = len(tokenizer.encode(final_response))
            except Exception as e:
                # 如果tokenizer编码失败，使用简单的空格分割计数
                completion_tokens = len(final_response.split())
        else:
            # 如果没有tokenizer，使用简单的空格分割计数
            prompt_tokens = len(prompt.split()) if isinstance(prompt, str) else 0
            completion_tokens = len(final_response.split())
        
        return RequestStats(
            prompt_id=prompt_index,
            request_start=start_time,
            ttft=ttft,
            request_end=end_time,
            successful=ttft > 0,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )


async def test_long_document_qa(
    client, model, prompts=None, output_len=100, max_inflight_requests=10, tokenizer=None
):
    """
    Test long document QA with the given prompts and sampling parameters.
    Process prompts concurrently with a limit on inflight requests.

    Args:
        client: The OpenAI client for making API calls.
        model: The model name to use for generation.
        prompts: A list of prompt strings to be processed by the LLM.
        output_len: The maximum number of tokens to generate.
        max_inflight_requests: Maximum number of concurrent requests.
        tokenizer: Tokenizer for counting tokens.

    Returns:
        list: request_stats - a list of RequestStats objects
    """
    # Create semaphore to limit concurrent requests
    semaphore = asyncio.Semaphore(max_inflight_requests)

    # Create tasks for all prompts
    tasks = []
    for i, prompt in enumerate(prompts):
        task = process_single_prompt(
            client=client,
            model=model,
            prompt=prompt,
            prompt_index=i,
            total_prompts=len(prompts),
            output_len=output_len,
            semaphore=semaphore,
            tokenizer=tokenizer,
        )
        tasks.append(task)

    # Execute all tasks concurrently and collect results
    request_stats = await asyncio.gather(*tasks)

    return request_stats


def generate_warmup_prompt_ids(
    doc_prompts, sys_prompts, query_prompts, blend_special_str, tokenizer, offset=1
):
    blend_special_ids = tokenizer.encode(blend_special_str)[offset:]
    warmup_prompt_ids = []
    for doc_prompt, sys_prompt, query_prompt in zip(
        doc_prompts, sys_prompts, query_prompts
    ):
        sys_prompt_ids = tokenizer.encode(sys_prompt)
        doc_prompt_ids = tokenizer.encode(doc_prompt)[offset:]
        query_prompt_ids = tokenizer.encode(query_prompt)[offset:]
        warmup_prompt_ids.append(
            sys_prompt_ids
            + blend_special_ids
            + doc_prompt_ids
            + blend_special_ids
            + query_prompt_ids
        )
    return warmup_prompt_ids


def generate_prompt_ids(
    doc_prompts: list[str],
    sys_prompts: list[str],
    query_prompts: list[str],
    num_requests: int,
    num_docs_per_request: int,
    blend_special_str: str,
    tokenizer,
    offset: int = 1,
):
    blend_special_ids = tokenizer.encode(blend_special_str)[offset:]

    prompt_ids = []

    for i in range(num_requests):
        temp_prompt_ids = []
        sample_docs = random.sample(doc_prompts, num_docs_per_request)
        sample_docs_ids = [tokenizer.encode(doc)[offset:] for doc in sample_docs]
        sys_prompt_ids = tokenizer.encode(sys_prompts[i])
        query_prompt_ids = tokenizer.encode(query_prompts[i])[offset:]
        temp_prompt_ids += sys_prompt_ids
        for doc_ids in sample_docs_ids:
            temp_prompt_ids += blend_special_ids + doc_ids
        temp_prompt_ids += blend_special_ids + query_prompt_ids

        prompt_ids.append(temp_prompt_ids)

    return prompt_ids


async def main(args):
    random.seed(args.random_seed)

    # Create the OpenAI client
    if args.base_url:
        base_url = args.base_url
    else:
        base_url = f"http://localhost:{args.port}/v1"
    
    client = AsyncOpenAI(
        base_url=base_url, api_key="sk-dummy"
    )
    model = args.model
    blend_special_str = args.blend_special_str
    num_requests = args.num_requests
    num_docs_per_request = args.num_docs_per_request
    document_length = args.document_length
    num_total_documents = args.num_total_documents

    # 尝试加载data/model目录下的tokenizer
    try:
        tokenizer = AutoTokenizer.from_pretrained("data/model")
        print(f"Loaded tokenizer with vocab size: {tokenizer.vocab_size}")
    except Exception as e:
        print(f"Failed to load tokenizer: {e}")
        # 创建一个简单的分词器作为fallback
        class SimpleTokenizer:
            def encode(self, text):
                # 简单的分词：将文本按空格分割
                return text.split()
        tokenizer = SimpleTokenizer()
        print("Using simple tokenizer as fallback")

    doc_prompts = [
        str(i) + " " + " ".join(["hi"] * document_length)
        for i in range(num_total_documents)
    ]
    warmup_sys_prompts = ["You are a helpful assistant."] * num_total_documents
    warmup_query_prompts = ["What's up? how are you recently?"] * num_total_documents

    # Create warmup prompts as text strings
    warmup_prompt_ids = []
    for doc_prompt, sys_prompt, query_prompt in zip(
        doc_prompts, warmup_sys_prompts, warmup_query_prompts
    ):
        warmup_prompt = sys_prompt + blend_special_str + doc_prompt + blend_special_str + query_prompt
        warmup_prompt_ids.append(warmup_prompt)

    sys_prompts = ["You are a helpful assistant."] * num_requests
    query_prompts = ["What's up? how are you recently?"] * num_requests

    # Create benchmark prompts as text strings
    prompt_ids = []
    for i in range(num_requests):
        sample_docs = random.sample(doc_prompts, num_docs_per_request)
        prompt = sys_prompts[i]
        for doc in sample_docs:
            prompt += blend_special_str + doc
        prompt += blend_special_str + query_prompts[i]
        prompt_ids.append(prompt)

    write_resp("------warm up round------\n")
    warmup_start_time = time.time()
    warmup_request_stats = await test_long_document_qa(
        client=client,
        model=model,
        prompts=warmup_prompt_ids,
        output_len=args.output_len,
        max_inflight_requests=args.max_inflight_requests,
        tokenizer=tokenizer,
    )
    warmup_end_time = time.time()
    write_resp("------query round------\n")

    sleep_time_after_warmup = args.sleep_time_after_warmup
    if sleep_time_after_warmup > 0:
        write_resp(f"Sleeping for {sleep_time_after_warmup} seconds after warmup...\n")
        time.sleep(sleep_time_after_warmup)

    benchmark_start_time = time.time()
    benchmark_request_stats = await test_long_document_qa(
        client=client,
        model=model,
        prompts=prompt_ids,
        output_len=args.output_len,
        max_inflight_requests=args.max_inflight_requests,
        tokenizer=tokenizer,
    )
    benchmark_end_time = time.time()

    # Create DataFrames from request stats
    warmup_df = pd.DataFrame([stats.__dict__ for stats in warmup_request_stats])
    benchmark_df = pd.DataFrame([stats.__dict__ for stats in benchmark_request_stats])

    # Calculate token usage and other metrics
    total_prompt_tokens = benchmark_df['prompt_tokens'].sum()
    total_completion_tokens = benchmark_df['completion_tokens'].sum()
    query_duration = benchmark_end_time - benchmark_start_time
    
    # Calculate TTFT stats (convert to milliseconds)
    ttft_values = benchmark_df.query("successful == True")['ttft'].values * 1000
    mean_ttft = ttft_values.mean() if len(ttft_values) > 0 else 0
    min_ttft = ttft_values.min() if len(ttft_values) > 0 else 0
    max_ttft = ttft_values.max() if len(ttft_values) > 0 else 0
    
    # Calculate request latency stats
    request_latencies = (benchmark_df['request_end'] - benchmark_df['request_start']).values
    mean_latency = request_latencies.mean() if len(request_latencies) > 0 else 0
    min_latency = request_latencies.min() if len(request_latencies) > 0 else 0
    max_latency = request_latencies.max() if len(request_latencies) > 0 else 0
    
    # Calculate throughput
    input_throughput = total_prompt_tokens / query_duration if query_duration > 0 else 0
    output_throughput = total_completion_tokens / query_duration if query_duration > 0 else 0
    
    # Print results in the requested format
    print(f"平均TTFT: {mean_ttft:.4f}毫秒")
    print(f"最小TTFT: {min_ttft:.4f}毫秒")
    print(f"最大TTFT: {max_ttft:.4f}毫秒")
    print(f"输入token吞吐率: {input_throughput:.2f} tokens/秒")
    print(f"输出token吞吐率: {output_throughput:.2f} tokens/秒")
    print(f"平均单个请求延迟总时间: {mean_latency:.4f}秒")
    print(f"最小单个请求延迟总时间: {min_latency:.4f}秒")
    print(f"最大单个请求延迟总时间: {max_latency:.4f}秒")
    print(f"所有请求耗时: {query_duration:.4f}秒")
    print(f"所有请求输入token总数: {total_prompt_tokens}")
    print(f"所有请求输出token总数: {total_completion_tokens}")

    # Validate expected gains as multiplicative speed-ups
    if args.expected_ttft_gain is not None:
        warmup_mean_ttft = warmup_df.query("successful == True")['ttft'].mean()
        query_mean_ttft = benchmark_df.query("successful == True")['ttft'].mean()
        actual_ttft_gain = (
            warmup_mean_ttft / query_mean_ttft if query_mean_ttft > 0 else float("inf")
        )
        print(f"Actual TTFT gain: {actual_ttft_gain:.2f}×")
        if actual_ttft_gain < args.expected_ttft_gain:
            sys.exit(
                f"ERROR: TTFT gain {actual_ttft_gain:.2f}× < expected "
                f"{args.expected_ttft_gain:.2f}×"
            )

    if args.expected_latency_gain is not None:
        warmup_duration = warmup_end_time - warmup_start_time
        query_duration = benchmark_end_time - benchmark_start_time

        # compute per-prompt latency before comparing
        warmup_per_prompt = warmup_duration / len(warmup_request_stats)
        query_per_prompt = query_duration / len(benchmark_request_stats)
        actual_latency_gain = (
            warmup_per_prompt / query_per_prompt
            if query_per_prompt > 0
            else float("inf")
        )
        print(f"Actual latency gain: {actual_latency_gain:.2f}×")
        if actual_latency_gain < args.expected_latency_gain:
            sys.exit(
                f"ERROR: latency gain {actual_latency_gain:.2f}× < expected "
                f"{args.expected_latency_gain:.2f}×"
            )


def create_argument_parser():
    parser = argparse.ArgumentParser(
        description="Benchmark the performance forMulti-Doc QA."
    )
    
    parser.add_argument(
        "--base-url",
        type=str,
        default=None,
        help="Base URL to query the LLM server (exclusive with --port)",
    )

    parser.add_argument(
        "--document-length",
        type=int,
        # Roughly the number of tokens for a system paper,
        # excluding images
        default=3000,
        help="Length of each document in tokens.",
    )

    parser.add_argument(
        "--num-total-documents",
        type=int,
        default=100,
        help="Number of documents to generate for testing.",
    )

    parser.add_argument(
        "--output-len",
        type=int,
        default=10,
        help="Maximum number of tokens to generate for each prompt.",
    )

    parser.add_argument(
        "--num-requests",
        type=int,
        default=100,
        help="Number of requests to send.",
    )

    parser.add_argument(
        "--num-docs-per-request",
        type=int,
        default=5,
        help="Number of requests to send.",
    )

    parser.add_argument(
        "--sampling-strategy",
        type=str,
        default="random",
        help="Random seed for sampling",
    )

    parser.add_argument(
        "--random-seed",
        type=int,
        default=0,
        help='Random seed when the repeat mode is "random"',
    )

    parser.add_argument(
        "--blend-special-str",
        type=str,
        default=" # # ",
        help="Special string to separate different documents.",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to query the vLLM server",
    )

    parser.add_argument(
        "--model",
        type=str,
        default="meta-llama/Llama-3.1-8B-Instruct",
        help="Model name",
    )

    parser.add_argument(
        "--max-inflight-requests",
        type=int,
        default=20,
        help="Maximum number of concurrent inflight requests",
    )

    parser.add_argument(
        "--sleep-time-after-warmup",
        type=float,
        default=0.0,
        help="Sleep time after warm up iteration",
    )

    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Filename to write all responses to; if omitted, writes to stdout.",
    )
    parser.add_argument(
        "--expected-ttft-gain",
        type=float,
        default=None,
        help=(
            "Expected minimum speed-up in time-to-first-token (warmup/query) "
            "as a factor, e.g. 4.3 for 4.3×. If actual gain is below this, exits."
        ),
    )
    parser.add_argument(
        "--expected-latency-gain",
        type=float,
        default=None,
        help=(
            "Expected minimum speed-up in total round time (warmup/query) "
            "as a factor, e.g. 4.5 for 4.5×. If actual gain is below this, exits."
        ),
    )

    return parser


if __name__ == "__main__":
    parser = create_argument_parser()
    args = parser.parse_args()
    OUTPUT_FILE = args.output
    asyncio.run(main(args))
