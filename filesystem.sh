# python -m pipeline --exp-name exp --mcp filesystem --tasks all --models gpt-5 --k 1
# python -m pipeline --exp-name budget_computation --mcp filesystem --tasks folder_structure/structure_analysis --models claude-sonnet-4.5 --k 1
# python -m pipeline --exp-name budget_computation --mcp filesystem --tasks legal_document/solution_tracing --models claude-sonnet-4.5 --k 1
# python -m pipeline --exp-name author_folders --mcp filesystem --tasks papers/author_folders --models claude-sonnet-4.5 --k 1
# python -m pipeline --exp-name find_math_paper --mcp filesystem --tasks papers/find_math_paper --models claude-sonnet-4.5 --k 1
# python -m pipeline --exp-name organize_legacy_papers --mcp filesystem --tasks papers/organize_legacy_papers --models claude-sonnet-4.5 --k 1

# [succeed] python -m pipeline --exp-name english_talent --mcp filesystem --tasks student_database/english_talent --models claude-sonnet-4.5 --k 1

# python -m pipeline --exp-name gradebased_score --mcp filesystem --tasks student_database/gradebased_score --models claude-sonnet-4.5 --k 1


# python -m pipeline --exp-name output_analysis --mcp filesystem --tasks threestudio/output_analysis --models claude-sonnet-4.5 --k 1
# python -m pipeline --exp-name requirements_completion --mcp filesystem --tasks threestudio/requirements_completion --models claude-sonnet-4.5 --k 1
# [succeed] python -m pipeline --exp-name debugging --mcp filesystem --tasks votenet/debugging --models claude-sonnet-4.5 --k 1
# python -m pipeline --exp-name requirements_writing --mcp filesystem --tasks votenet/requirements_writing --models claude-sonnet-4.5 --k 1



# python -m pipeline --exp-name new-gpt5 --mcp filesystem --tasks folder_structure/structure_analysis --models gpt-5 --k 3 
# python -m pipeline --exp-name new-gpt5 --mcp filesystem --tasks legal_document/solution_tracing --models gpt-5 --k 3 
# python -m pipeline --exp-name new-gpt5 --mcp filesystem --tasks papers/author_folders --models gpt-5 --k 3 
# python -m pipeline --exp-name new-gpt5 --mcp filesystem --tasks papers/find_math_paper --models gpt-5 --k 3  
# python -m pipeline --exp-name new-gpt5 --mcp filesystem --tasks papers/organize_legacy_papers --models gpt-5 --k 3  

# # [succeed] python -m pipeline --exp-name new-gpt5 --mcp filesystem --tasks student_database/english_talent --models gpt-5 --k 3  

# python -m pipeline --exp-name new-gpt5 --mcp filesystem --tasks student_database/gradebased_score --models gpt-5 --k 3  


# python -m pipeline --exp-name new-gpt5 --mcp filesystem --tasks threestudio/output_analysis --models gpt-5 --k 3  
# python -m pipeline --exp-name new-gpt5 --mcp filesystem --tasks threestudio/requirements_completion --models gpt-5 --k 3  
# # [succeed] python -m pipeline --exp-name new-gpt5 --mcp filesystem --tasks votenet/debugging --models gpt-5 --k 3  
# python -m pipeline --exp-name new-gpt5 --mcp filesystem --tasks votenet/requirements_writing --models gpt-5 --k 3  

# python -m pipeline --exp-name file_context --mcp filesystem --tasks file_context --models gpt-5 --k 1

python -m pipeline --exp-name folder_structure --mcp filesystem --tasks folder_structure --models gpt-5 --k 1