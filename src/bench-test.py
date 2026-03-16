import threading
import time
import numpy as np
import requests
import traceback
import json
import csv
import os
from transformers import AutoTokenizer



def send_request(request_number, url, headers, data, request_time_list, num_tokens):
    try:
        start = time.time()
        first_token_time = 0
        n = 0
        response = requests.post(url, headers=headers, data=json.dumps(data), stream=True, timeout=600000)
        for chunk in response.iter_content(chunk_size=100000, decode_unicode=True):
            if not first_token_time:
                first_token_time = time.time()
            if chunk:
                n += 1

        num_tokens = n - 2
        end = time.time()
        request_time_list.append({"首token时延": first_token_time-start, "token数": num_tokens, "非首token时延": (end-first_token_time)/(num_tokens-1)})
        print(f"第{request_number}个请求，第{n}个token时延为{time.time() - start}")
    except Exception as e:
        print(e)
        traceback.print_exc()


def test_request(url, name, in_out_sets, batch_sizes, result_file, tokenizer):
    for input_len, output_len in in_out_sets:
        for batch_size in batch_sizes:
            request_time_list = []
            threads = []
            all_start = time.time()
            for i in range(1, batch_size+1):
                prompt_ids = np.random.randint(100, tokenizer.vocab_size-100, input_len).tolist()
                prompt = tokenizer.decode(prompt_ids)
                # print(prompt)

                data = {
                    "model": "Qwen/Qwen3.5-9B",
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": True,
                    "max_tokens": output_len,
                    "ignore_eos": True
                }
                thread = threading.Thread(target=send_request, args=(i-1, url, headers, data, request_time_list, output_len))
                threads.append(thread)
                thread.start()

            # 等待所有线程完成
            for thread in threads:
                thread.join()

            all_end = time.time()
            sum_token_latency = 0
            sum_num_tokens = 0
            non_first_token_latency_list = []
            first_time_latency_list = []
            token_throughput = 0
            spend = 0
            non_first_token_latency = 0

            print(len(request_time_list))

            if len(request_time_list) == batch_size:
                for req in request_time_list:
                    first_time_latency_list.append(req["首token时延"])
                    non_first_token_latency_list.append(req["非首token时延"])
                    token_throughput += req["token数"]
                max_first_time_latency = max(first_time_latency_list)
                avg_non_first_tokens_latency = sum(non_first_token_latency_list) / len(non_first_token_latency_list)

                csv_data = {"model": name, "输入长度": input_len, "输出长度": output_len, "并发数": batch_size, "总时延": all_end-all_start,
                                "最大首token时延": max_first_time_latency*1000, "平均非首token时延": avg_non_first_tokens_latency*1000,
                            "总吞吐": token_throughput/(all_end-all_start), "单请求吞吐": token_throughput/(all_end-all_start)/batch_size}
                print(csv_data)
                with open(result_file, "a", newline='', encoding="utf-8-sig") as csvfile:
                    filenames = ['model', '输入长度', '输出长度', '并发数', '总时延', '最大首token时延', '平均非首token时延', '总吞吐', '单请求吞吐']
                    writer = csv.DictWriter(csvfile, fieldnames=filenames)
                    writer.writerow(csv_data)
            else:
                print(f"model={name}, 并发数={batch_size}, 输入={input_len}, 输出={output_len} 请求失败")


if __name__ == '__main__':
    headers = {'Content-Type': 'application/json'}
    # model_path = "/home/pengzs/model/qwen3-8b"
    model_path = "Qwen/Qwen3.5-9B"

    #   获取模型token分词对象
    TOKENIZER_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'model')
    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_PATH)



    name_card = "qwen3-8b-RTX5090-hicache"
    URL = "http://199.103.6.2:38000/v1/chat/completions"
    Result_File = "/tmp/result_model.csv"
    # In_Out_Sets = [(128, 128),(256, 256),(1024, 1024),(2048, 2048),(128, 2048),(2048, 128)]
    # In_Out_Sets = [(128, 128),(256, 256),(1024, 1024),(2048, 2048),(128, 2048),(2048, 128)]
    In_Out_Sets = [(128, 128),(256, 256)]
    # In_Out_Sets = [(256, 256)]
    # In_Out_Sets = [(1024, 1024)]
    # In_Out_Sets = [(2048, 2048)]
    # In_Out_Sets = [(128, 2048)]
    # In_Out_Sets = [(2048, 128)]
    # In_Out_Sets = [(8192, 512)]
    # Batch_Sizes = [17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,
    #                33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,
    #                49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64]
    Batch_Sizes = [2,4,8,16,24,32,40,48, 56]

    test_request(URL, name_card, In_Out_Sets, Batch_Sizes, Result_File, tokenizer)







