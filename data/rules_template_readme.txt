规则导入模板说明

字段含义：
  id            唯一编号，建议「市场-类别-序号」，如 KR-ADL-01。重复会被拒绝。
  market        市场码，只能是 CN / EU / US / PH / KR / RU / MN 之一，或 * 表示全部市场
  category      品类，可选 *=全部 / cosmetic=化妆品 / supplement=膳食补充剂 / medical_device=医疗器械
  level         严重级别：L1（直接拦截）L2（自动改写）L3（放行）
  action        对应动作：block / rewrite / pass，需与 level 匹配
  clause        条款出处，写法规名和条款号。这块最重要，评委和法务会看
  trigger       一句话说明触发条件，给人看的中文描述
  patterns      中文触发词列表，可留空
  patterns_en   英文触发词列表，可留空
  exempt        例外情形，出现这些内容时不判违规

注意：
  1. patterns / patterns_en / patterns_regex 至少要填一个，否则这条规则不生效
  2. 英文触发词按词边界匹配，heal 不会命中 healthcare
  3. 导入前会逐条校验，报错会指出第几条、缺什么
  4. 导入后自动生成版本快照，可以在「版本回滚」里退回去
