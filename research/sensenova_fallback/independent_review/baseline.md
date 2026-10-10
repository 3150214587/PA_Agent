# 改动前独立基线

目录：D:\cl\PA_Agent
命令：python -m pytest tests/unit/test_deepseek_client.py -q
结果：26项中23通过、3失败；以下是修改前即存在的KKAI兼容断言失败，不属于本次SenseNova新增功能：
- test_chat_kkai_sends_thinking_object_not_reasoning_effort：实际thinking.type=adaptive，测试期望enabled和budget_tokens=999998。
- test_chat_kkai_thinking_off_sends_no_thinking_params：实际extra_body含disabled，测试期望无extra_body。
- test_stream_kkai_passes_thinking_extra_body：缺budget_tokens。

修改前已有未提交改动：pa_agent/ai/market_features.py、tests/unit/test_market_features.py、多份prompt_engineering文本、research/pa_validation及两份PA研究报告。不得清理或覆盖。

源码来源由浏览器实际打开核验：https://github.com/Ebony-Vinyl/dsh-our-free-model
src/kilo.js：公开免费池通过GET https://api.kilo.ai/api/gateway/models的isFree=true筛选；POST /chat/completions无鉴权。免费提示词可能被上游记录。
