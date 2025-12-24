# python -m pipeline --exp-name exp --mcp filesystem --tasks all --models gpt-5 --k 1
# python -m pipeline --exp-name budget_computation --mcp filesystem --tasks folder_structure/structure_analysis --models claude-sonnet-4.5 --k 1
# python -m pipeline --exp-name budget_computation --mcp filesystem --tasks legal_document/solution_tracing --models claude-sonnet-4.5 --k 1
# python -m pipeline --exp-name author_folders --mcp filesystem --tasks papers/author_folders --models claude-sonnet-4.5 --k 1
# python -m pipeline --exp-name find_math_paper --mcp filesystem --tasks papers/find_math_paper --models claude-sonnet-4.5 --k 1
# python -m pipeline --exp-name organize_legacy_papers --mcp filesystem --tasks papers/organize_legacy_papers --models claude-sonnet-4.5 --k 1


# python -m pipeline --exp-name new-gpt5 --mcp filesystem --tasks student_database/gradebased_score --models gpt-5 --k 3  


# python -m pipeline --exp-name new-gpt5 --mcp filesystem --tasks threestudio/output_analysis --models gpt-5 --k 3  
# python -m pipeline --exp-name new-gpt5 --mcp filesystem --tasks threestudio/requirements_completion --models gpt-5 --k 3  
# # [succeed] python -m pipeline --exp-name new-gpt5 --mcp filesystem --tasks votenet/debugging --models gpt-5 --k 3  
# python -m pipeline --exp-name new-gpt5 --mcp filesystem --tasks votenet/requirements_writing --models gpt-5 --k 3  

# python -m pipeline --exp-name file_context --mcp filesystem --tasks file_context --models gpt-5 --k 1

# python -m pipeline --exp-name folder_structure --mcp filesystem --tasks folder_structure --models gpt-5 --k 1


# python -m pipeline --exp-name test_shopping --mcp playwright_webarena --tasks shopping/advanced_product_analysis --models claude-sonnet-4.5 --k 1
# python -m pipeline --exp-name test_shopping --mcp playwright_webarena --tasks shopping/health_routine_optimization --models claude-sonnet-4.5 --k 1
# python -m pipeline --exp-name test_shopping --mcp playwright_webarena --tasks shopping/holiday_baking_competition --models claude-sonnet-4.5 --k 1


#下面的实验名字是test_shopping2，相比test_shopping的修改是：增加了一个simple_search的skill
# python -m pipeline --exp-name test_shopping2 --mcp playwright_webarena --tasks shopping/advanced_product_analysis --models claude-sonnet-4.5 --k 1
# python -m pipeline --exp-name test_shopping2 --mcp playwright_webarena --tasks shopping/health_routine_optimization --models claude-sonnet-4.5 --k 1
# python -m pipeline --exp-name test_shopping2 --mcp playwright_webarena --tasks shopping/holiday_baking_competition --models claude-sonnet-4.5 --k 1
# python -m pipeline --exp-name test_shopping2 --mcp playwright_webarena --tasks shopping/multi_category_budget_analysis --models claude-sonnet-4.5 --k 1
# python -m pipeline --exp-name test_shopping2 --mcp playwright_webarena --tasks shopping/gaming_accessories_analysis --models claude-sonnet-4.5 --k 1
# python -m pipeline --exp-name test_shopping2 --mcp playwright_webarena --tasks shopping/printer_keyboard_search --models claude-sonnet-4.5 --k 1
# python -m pipeline --exp-name test_shopping2 --mcp playwright_webarena --tasks shopping/running_shoes_purchase --models claude-sonnet-4.5 --k 1

#下面的实验名字是test_shopping3，相比test_shopping2的修改是：使用gpt5模型
# python -m pipeline --exp-name test_shopping3 --mcp playwright_webarena --tasks shopping/advanced_product_analysis --models gpt-5 --k 1
# python -m pipeline --exp-name test_shopping3 --mcp playwright_webarena --tasks shopping/health_routine_optimization --models gpt-5 --k 1
# python -m pipeline --exp-name test_shopping3 --mcp playwright_webarena --tasks shopping/holiday_baking_competition --models gpt-5 --k 1
# python -m pipeline --exp-name test_shopping3 --mcp playwright_webarena --tasks shopping/multi_category_budget_analysis --models gpt-5 --k 1


# python -m pipeline --exp-name test_shopping_admin --mcp playwright_webarena --tasks shopping_admin/customer_segmentation_setup --models claude-sonnet-4.5 --k 1
# python -m pipeline --exp-name test_shopping_admin --mcp playwright_webarena --tasks shopping_admin/marketing_customer_analysis --models claude-sonnet-4.5 --k 1
python -m pipeline --exp-name test_shopping_admin --mcp playwright_webarena --tasks shopping_admin/search_filtering_operations --models claude-sonnet-4.5 --k 1
# python -m pipeline --exp-name test_shopping_admin --mcp playwright_webarena --tasks shopping_admin/fitness_promotion_strategy --models claude-sonnet-4.5 --k 1
# python -m pipeline --exp-name test_shopping_admin --mcp playwright_webarena --tasks shopping_admin/marketing_customer_analysis --models claude-sonnet-4.5 --k 1
# python -m pipeline --exp-name test_shopping_admin --mcp playwright_webarena --tasks shopping_admin/search_filtering_operations --models claude-sonnet-4.5 --k 1


# python -m pipeline --exp-name test_reddit_show --mcp playwright_webarena --tasks reddit/budget_europe_travel --models claude-sonnet-4.5 --k 1
# python -m pipeline --exp-name test_reddit --mcp playwright_webarena --tasks reddit/ai_data_analyst --models claude-sonnet-4.5 --k 1
# python -m pipeline --exp-name test_reddit --mcp playwright_webarena --tasks reddit/buyitforlife_research --models claude-sonnet-4.5 --k 1
# python -m pipeline --exp-name test_reddit --mcp playwright_webarena --tasks reddit/llm_research_summary --models claude-sonnet-4.5 --k 3
# python -m pipeline --exp-name test_reddit --mcp playwright_webarena --tasks reddit/routine_tracker_forum --models claude-sonnet-4.5 --k 1
# python -m pipeline --exp-name test_reddit --mcp playwright_webarena --tasks reddit/movie_reviewer_analysis --models claude-sonnet-4.5 --k 1
# python -m pipeline --exp-name test_reddit --mcp playwright_webarena --tasks reddit/nba_statistics_analysis --models claude-sonnet-4.5 --k 1


# python -m pipeline --exp-name test_playwright --mcp playwright --tasks eval_web/cloudflare_turnstile_challenge --models claude-sonnet-4.5 --k 1
# python -m pipeline --exp-name test_playwright --mcp playwright_webarena --tasks eval_web/extraction_table --models claude-sonnet-4.5 --k 1
# python -m pipeline --exp-name test_playwright --mcp playwright_webarena --tasks web_search/birth_of_arvinxu --models claude-sonnet-4.5 --k 1
# python -m pipeline --exp-name test_playwright --mcp playwright_webarena --tasks web_search/r1_arxiv --models claude-sonnet-4.5 --k 1