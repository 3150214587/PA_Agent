# 独立验收清单

- 精确SenseNova URL gate；主接口成功不尝试免费池；其他provider不受影响。
- 普通异常覆盖：429、连接失败、超时、5xx、空响应、非法JSON、字段/结构校验失败。
- 合法wait/reject不当失败；不降低交易安全校验；取消与进程级中断向上传递。
- 免费列表严格isFree=true；候选先滤冷却再限数量；排除安全分类专用小模型；无候选时清晰失败。
- 仅用公开免密Kilo足够，已独立实测Ling3.1和Nemotron3.5-lightning HTTP200、合法JSON、cost0。无需引入OpenCode伪装工具/客户端指纹协议。
- 真实端到端必须走正常提示词组装+校验+记录，主接口故障可注入，但免费请求不得mock；标清合成行情与实际API回复。
- 保留完整请求、响应、异常、来源模型、测试记录，不保存生产key。
- 既有基线：deepseek_client 23过3个KKAI失败；直接相关两阶段/validation_retry 19通过。
- 全integration基线另有11失败（4行情外网、2旧预测字段、4Qt绑定、1不下单价位），保存在baseline-integration.log。不要把这些算为新增回归。
