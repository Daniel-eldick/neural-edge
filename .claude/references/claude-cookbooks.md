# Claude Cookbooks Reference

Curated patterns from Anthropic's official [Claude Cookbooks](https://github.com/anthropics/claude-cookbooks) (33k+ stars, MIT licensed).

Use during `/brainstorm`, `/plan`, and `/diagnose` sessions to reference proven patterns instead of reinventing.

**Website**: https://platform.claude.com/cookbook/
**Repo**: https://github.com/anthropics/claude-cookbooks

---

## Agent Patterns

| Pattern | Link | When to reference |
|---------|------|-------------------|
| Agent architectures | [patterns/agents/](https://github.com/anthropics/claude-cookbooks/tree/main/patterns/agents) | Planning multi-step features, orchestration design |
| Claude Agent SDK | [claude_agent_sdk/](https://github.com/anthropics/claude-cookbooks/tree/main/claude_agent_sdk) | Building custom agents (e.g., WhatsApp/Telegram bot) |
| Sub-agents (Haiku as helper) | [multimodal/using_sub_agents.ipynb](https://github.com/anthropics/claude-cookbooks/blob/main/multimodal/using_sub_agents.ipynb) | Delegating subtasks to smaller models for cost/speed |
| Customer service agent | [tool_use/customer_service_agent.ipynb](https://github.com/anthropics/claude-cookbooks/blob/main/tool_use/customer_service_agent.ipynb) | Customer-facing AI features, chatbot design |

## Tool Use

| Pattern | Link | When to reference |
|---------|------|-------------------|
| Tool use basics | [tool_use/](https://github.com/anthropics/claude-cookbooks/tree/main/tool_use) | Any feature involving Claude calling external APIs/tools |
| Calculator tool | [tool_use/calculator_tool.ipynb](https://github.com/anthropics/claude-cookbooks/blob/main/tool_use/calculator_tool.ipynb) | Structured tool definitions, input validation |
| SQL queries with Claude | [misc/how_to_make_sql_queries.ipynb](https://github.com/anthropics/claude-cookbooks/blob/main/misc/how_to_make_sql_queries.ipynb) | AI-generated database queries, natural language to SQL |
| Tool evaluation | [tool_evaluation/](https://github.com/anthropics/claude-cookbooks/tree/main/tool_evaluation) | Measuring tool call accuracy, evaluating agent performance |

## RAG & Retrieval

| Pattern | Link | When to reference |
|---------|------|-------------------|
| RAG techniques | [capabilities/retrieval_augmented_generation/](https://github.com/anthropics/claude-cookbooks/tree/main/capabilities/retrieval_augmented_generation) | Features needing knowledge retrieval (menu search, FAQ) |
| Embeddings (VoyageAI) | [third_party/VoyageAI/](https://github.com/anthropics/claude-cookbooks/tree/main/third_party/VoyageAI) | Semantic search, similarity matching |
| Pinecone RAG | [third_party/Pinecone/](https://github.com/anthropics/claude-cookbooks/tree/main/third_party/Pinecone) | Vector database integration for search |

## Classification & Summarization

| Pattern | Link | When to reference |
|---------|------|-------------------|
| Classification | [capabilities/classification/](https://github.com/anthropics/claude-cookbooks/tree/main/capabilities/classification) | Auto-categorizing orders, menu items, customer feedback |
| Summarization | [capabilities/summarization/](https://github.com/anthropics/claude-cookbooks/tree/main/capabilities/summarization) | Order analytics summaries, trend reports |

## Multimodal

| Pattern | Link | When to reference |
|---------|------|-------------------|
| Vision getting started | [multimodal/getting_started_with_vision.ipynb](https://github.com/anthropics/claude-cookbooks/blob/main/multimodal/getting_started_with_vision.ipynb) | Image-based features (menu photo analysis, receipt scanning) |
| Charts & graphs | [multimodal/reading_charts_graphs_powerpoints.ipynb](https://github.com/anthropics/claude-cookbooks/blob/main/multimodal/reading_charts_graphs_powerpoints.ipynb) | Analytics visualization interpretation |
| Text transcription | [multimodal/how_to_transcribe_text.ipynb](https://github.com/anthropics/claude-cookbooks/blob/main/multimodal/how_to_transcribe_text.ipynb) | OCR, document processing |

## Quality & Evaluation

| Pattern | Link | When to reference |
|---------|------|-------------------|
| Building evals | [misc/building_evals.ipynb](https://github.com/anthropics/claude-cookbooks/blob/main/misc/building_evals.ipynb) | Testing AI feature quality, regression detection |
| Moderation filter | [misc/building_moderation_filter.ipynb](https://github.com/anthropics/claude-cookbooks/blob/main/misc/building_moderation_filter.ipynb) | Content filtering for user-generated content |
| JSON mode | [misc/how_to_enable_json_mode.ipynb](https://github.com/anthropics/claude-cookbooks/blob/main/misc/how_to_enable_json_mode.ipynb) | Structured output from AI features |

## Performance & Cost

| Pattern | Link | When to reference |
|---------|------|-------------------|
| Prompt caching | [misc/prompt_caching.ipynb](https://github.com/anthropics/claude-cookbooks/blob/main/misc/prompt_caching.ipynb) | Reducing API costs for repeated prompts |
| Extended thinking | [extended_thinking/](https://github.com/anthropics/claude-cookbooks/tree/main/extended_thinking) | Complex reasoning tasks, multi-step analysis |
| Observability | [observability/](https://github.com/anthropics/claude-cookbooks/tree/main/observability) | Monitoring AI feature usage and costs |

---

## How to Use This File

- **During `/brainstorm` Phase 3 (Ideate)**: Scan categories above for relevant patterns before generating options
- **During `/plan` Step 2 (Context Gathering)**: Check if a cookbook pattern applies to the architecture being planned
- **During `/diagnose`**: Check Quality & Evaluation section for debugging and eval patterns
- **To fetch details**: Use `WebFetch` on any link above to read the full notebook content
