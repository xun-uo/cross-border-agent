# 跨境智服 Agent

面向中小跨境卖家的**买家侧客服 Agent**：用买家语言回答物流/退换货/商品问题，并在每次回复发出前按「目标市场 + 商品品类」完成合规判定——违规表述自动改写，硬违规拦截为安全话术或转人工。

> 第二届全国人工智能应用创新大赛参赛作品。

## 当前状态

| 模块 | 状态 |
|---|---|
| 合规规则表（CN/EU/US 各 8 条，共 24 条） | ✅ |
| 合规四级流水线（切分宣称 → 语境判定 → 规则匹配 → 分级动作） | ✅ |
| 意图识别（主意图 + flags + 情绪，含 order_change） | ✅ 90% |
| 订单与物流工具（20 条 Mock 订单，10 种状态） | ✅ |
| 自动改写 + 复检 | ✅ |
| Streamlit 演示界面（对话 + trace 面板 + 口令 + 每日限额） | ✅ |
| 评测集 60 条 + 留出集 15 条 | ✅ |
| FastAPI 接口 | ⬜ |
| 公网部署（评委可访问） | ⬜ |

## 快速开始

### 1. 配置密钥

`apikey.txt` 里只放 key 原文，或 `.env` 写 `DEEPSEEK_API_KEY=sk-xxx`。

### 2. 启动演示界面

双击 `启动演示.cmd`，或：

```bash
.venv\Scripts\python.exe -m streamlit run web\app.py --server.port 8501
```

浏览器打开 <http://127.0.0.1:8501>，口令 `xinghe2026`。

### 3. 跑端到端脚本

```bash
python scripts\gen_rules.py     # 生成合规规则
python scripts\gen_mock.py      # 生成订单/商品/手册
python scripts\gen_testset.py   # 生成评测集
python run_demo.py              # 7 个演示场景
python scripts\eval.py          # 评测（--no-llm 只跑合规）
python scripts\holdout.py       # 留出集盲测
```

## 目录结构

```
跨境智服/
├─ apikey.txt              API key（不要提交到仓库）
├─ run_demo.py             端到端演示脚本
├─ start_web.ps1           界面启动脚本
├─ 启动演示.cmd            双击入口
├─ app/
│  ├─ config.py            配置与密钥读取
│  ├─ llm.py               DeepSeek 客户端（仅标准库）
│  ├─ compliance.py        合规四级流水线 + 改写
│  └─ agent.py             意图 → 工具 → 生成 → 合规 → 动作
├─ data/
│  ├─ rules.json           24 条合规规则
│  ├─ orders.json          20 条 Mock 订单
│  ├─ products.json        商品（含敏感品类）
│  ├─ kb.json              产品手册与政策片段
│  └─ testset.json         60 条评测集 + 50 条意图标注
├─ web/
│  └─ app.py               Streamlit 演示界面
├─ scripts/
│  ├─ gen_rules.py         规则表生成器
│  ├─ gen_mock.py          订单/商品/手册生成器
│  ├─ gen_testset.py       评测集生成器
│  ├─ eval.py              评测脚本
│  ├─ holdout.py           留出集盲测
│  └─ ui_test.py           界面逻辑测试
└─ out/                    运行产物
```

## 合规规则结构

每条规则是一行结构化数据，不是关键词堆：

```json
{
  "id": "US-FDA-101",
  "market": "US",
  "category": "supplement",
  "level": "L2",
  "action": "rewrite",
  "clause": "21 CFR 101.93",
  "trigger": "结构功能声明未加免责声明",
  "patterns_en": ["supports sleep", "promotes relaxation"],
  "patterns_regex": ["\\b(?:faster|better|cheaper)\\s+than\\s+(?:any|every|all)\\b"],
  "exempt": ["not intended to diagnose, treat, cure, or prevent any disease"],
  "requires": ["not intended to diagnose", "not evaluated by the fda"]
}
```

- `patterns / patterns_en`：子串触发
- `patterns_regex`：泛化模式，避免枚举式漏判（动词+疾病实体、比较级+than any）
- `exempt`：句子自身含这些表述即豁免
- `requires`：**条件型规则**——全文满足前置条件（如已附免责声明）则不判违规

## 三类规则机制

| 机制 | 解决什么 | 例子 |
|---|---|---|
| 禁止型 | 出现即违规 | 绝对化用语、疾病宣称 |
| 条件型（requires） | 必须同时满足前置条件 | 结构功能声明未附 DSHEA 免责 |
| 否定语境判定 | 通用规则，非逐条枚举 | “本产品**不能**治疗……”应放行 |

否定语境判定：触发词落在 `not / cannot / 不承诺 / 无法` 的语境里即豁免。
这一条把误杀率从 20% 降到 0%，且是**通用规则**——没见过的合规话术也能正确放行。

## 评测结果

主集 60 条（红线 20 / 擦边 20 / 陷阱 20）：

| 指标 | 结果 | 目标 |
|---|---|---|
| 红线漏杀率 | 0% | ≤5% |
| 红线严格拦截率（block） | 80% | — |
| 误杀率 | 0% | ≤10% |
| 擦边识别率 | 95% | ≥80% |
| 主意图准确率 | 90%（45/50） | ≥85% |

留出集 15 条盲测：第一次 60%（红线 1/4、陷阱 5/5、擦边 3/6），改成正则泛化后 15/15。
**15/15 不能算泛化**，因为改进依据来自留出集的失败项。真实水平介于两者之间。

## 已知边界

- 规则层依赖表述模式，未覆盖的修辞变体仍可能漏判——这是纯规则方案的天花板。
- 补齐路径是加 LLM 语义兜底层，本次未实施（工期与回归风险）。
- 条款编号为技术示例，正式提交前须核对官方原文。
- 数据全部为 Mock，未接入真实平台。
- 语种支持 en / es（de / fr 结构预留）。
