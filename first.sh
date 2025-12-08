python -m pipeline \
  --mcp filesystem \
  --k 1 \
  --models gpt-5 \
  --tasks file_property/size_classification
# Add --task-suite easy to run the lightweight dataset (where available)