# 本机资料读取契约

本契约不包含真实经营规则或案例。两个私有库共享同一根目录；库内引用不得逃出各自仓库。库的DATASET.json是格式身份标记，不是加密访问控制或真假资料的签名认证。

## 共用身份标记

DATASET.json必须含`dataset`（分别为`timemix_rules`、`timemix_cases`）、`schema_version: 1`、非空`version`及`required_files`数组，必须包含INDEX.md。逐项实际读取清单文件，空文件或缺失拒绝使用。不能只检查目录存在。

## Rules

- 读取INDEX，检查所列本地文件均存在可读、没有越出Rules库。
- `current/`非空，规则Markdown含唯一`id: RULE_*`和`status: active`。
- 生效日期可能留空，不补猜。读取相关规则正文及PENDING中的相关空白后才能决定业务口径。
- `content_state`标识已发布或本地补充状态；不把标签版本相同说成内容相同。

## Cases

- INDEX、SCHEMA、TAXONOMY、MANIFEST.json、raw_manifest.json及DATASET所列文件可读。
- MANIFEST的case_ids不重复，case_count与列表和实际CASE文件一致，version与DATASET一致。
- CASE_YYYY_NNN文件元数据case_id与文件名一致、业务status为closed；review_status为approved/reviewed/needs_review之一。后者仅供待审核参考，不混同业务状态。
- CASE正文所引库内文件必须可读。原件按raw_manifest逐项验证路径、字节数及SHA-256；保持原始文件，不按个人猜测修复。
- historical相关Rule和today相关Rule入口分开；SCHEMA定义的字段优先，不要求旧示例字段名与当前结构完全相同。

无脚本能力时以上检查需要平台实际文件读写/校验工具完成；无法完成时说明限制并停止，不用口头确认替代。平台能看到上传附件不等于能读取电脑默认目录，不能据此绕过本机资料模式。
