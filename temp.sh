curl -X POST http://0.0.0.0:4000/v1/messages \
-H "Authorization: Bearer sk-3blkZv71U7lH1TQbVNOX6A" \
-H "Content-Type: application/json" \
-d '{
    "model": "openai/gzy/claude-4.5-sonnet",
    "max_tokens": 1000,
    "messages": [{"role": "user", "content": "Hi"}]
}'