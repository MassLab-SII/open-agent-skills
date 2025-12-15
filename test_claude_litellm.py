import openai

client = openai.OpenAI(
	api_key="sk-3blkZv71U7lH1TQbVNOX6A",
	base_url="http://101.47.31.49:4000"
)

# Example with text only
response = client.chat.completions.create(
    model="gzy/claude-4.5-sonnet",
    messages=[
        {
            "role": "user",
            "content": "Hi"
        }
    ],
    reasoning_effort = "medium",
    temperature = 1,
)

print(response)

# from litellm import completion

# response = completion(
#     # 如果你的中转站要求模型名必须保持原样，建议添加 custom_llm_provider="openai"
#     model="gzy/claude-4.5-sonnet", 
#     messages=[
#         {
#             "role": "user",
#             "content": "Hi"
#         }
#     ],
#     api_key="sk-3blkZv71U7lH1TQbVNOX6A",
#     api_base="http://101.47.31.49:4000",  # 注意：这里参数名变成了 api_base
#     custom_llm_provider="openai"          # 关键点：告诉 litellm 使用 OpenAI 的协议格式去请求这个地址
# )

# print(response)


# from litellm import completion

# response = completion(
#     # 在模型名称前加 "openai/"，litellm 会自动识别为 OpenAI 协议并去连接 api_base
#     model="openai/gzy/claude-4.5-sonnet",
#     messages=[
#         {
#             "role": "user",
#             "content": "Hi"
#         }
#     ],
#     api_key="sk-3blkZv71U7lH1TQbVNOX6A",
#     api_base="http://101.47.31.49:4000"
# )

# print(response)