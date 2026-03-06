import random
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("data/model")

print(tokenizer.vocab_size)

print(tokenizer("你好,我有个问题。I have a question"))
print(tokenizer.decode(tokenizer("你好")["input_ids"]))

print("-" * 10)
random_token_id = random.randint(1, tokenizer.vocab_size)
print(tokenizer.decode([random_token_id]))

random.randint(1, tokenizer.vocab_size)
idarr = [random.randint(1, tokenizer.vocab_size) for idx in range(10)]
str = tokenizer.decode(idarr)
print(str)
print(idarr)

token_ids = tokenizer(str)
print(token_ids["input_ids"])





 
