# 本机资料读取契约

本契约不包含真实经营规则或案例。两个私有库共享同一根目录；库内引用不得逃出各自仓库。库的DATASET.json是格式身份标记，不是加密访问控制或真假资料的签名认证。

## 共用身份标记

DATASET.json必须含`dataset`（分别为`timemix_rules`、`timemix_cases`）、`schema_version`（Rules为1，Cases为2）、非空`version`及`required_files`数组，必须包含INDEX.md。逐项实际读取清单文件，空文件或缺失拒绝使用。不能只检查目录存在。

## Rules

- 读取INDEX，检查所列本地文件均存在可读、没有越出Rules库。
- `current/`非空，规则Markdown含唯一`id: RULE_*`和`status: active`。
- 生效日期可能留空，不补猜。读取相关规则正文及PENDING中的相关空白后才能决定业务口径。
- `content_state`标识已发布或本地补充状态；不把标签版本相同说成内容相同。

## Cases

- INDEX、SCHEMA、TAXONOMY、MANIFEST及DATASET所列文件可读；Cases的schema_version必须为2。旧格式需要用户明确更新，不混读两套目录。
- 每案目录`CASE_YYYY_NNN/case.md`，可选同目录records.md；MANIFEST的case_ids唯一，case_count与实际目录一致，version与DATASET一致。
- case头部含case_id、title、legacy_ids、issue_type、tags、status、date；case_id与目录一致，status为closed。正文含案件事实、客户诉求、实际处理结果、处理依据。
- discretion可选，只有granted/denied；owner_judgment有值时必须有discretion，不由检查器判定其真实性。历史破例不自动授权新的例外。
- 校验Case和records的库内链接及MANIFEST files列出的字节数和SHA-256，清单与实际文字文件一致。校验失败不重算清单来掩盖变化。
- 不依赖raw_manifest、云端截图、老板/AI完整讨论或旧review_status字段。旧cases/chats/raw/sources目录不作为新库内容保留。
- records只能存实际聊天和相关记录，结构检查能发现部分AI讨论标记，不能代替人工内容纯度核查。老板后续确认放Case，拟稿不能当实际发送。

无脚本能力时以上检查需要平台实际文件读写/校验工具完成；无法完成时说明限制并停止，不用口头确认替代。平台能看到上传附件不等于能读取电脑默认目录，不能据此绕过本机资料模式。

## 初始化边界

缺失资料库按SKILL中的固定私有来源下载到同一根目录，再完成本契约所有检查；已有目录不覆盖。资料身份标记和完整性检查不替代GitHub访问授权。初始化失败不得绕过本机资料模式。日常检查仍然只读离线，显式更新后重新核验。
