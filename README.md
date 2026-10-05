# TimeMix售后Skill

本项目计划公开分发。Skill位于`timemix-after-sales/`，将整个文件夹导入支持自定义Skill的工具。日常处理所需的Rules和Cases单独保持私有，未包含在本目录。

使用者自行将获授权的两个资料库下载到同一资料根目录：

```text
资料根目录/
├── timemix_rules/
└── timemix_cases/
```

macOS默认：用户目录下`Documents/Obsidian/TimeMix/`。
Windows默认：系统实际文档目录下`timemix/TimeMixData/`。
其他位置通过`TIMEMIX_DATA_ROOT`或本次明确路径指定。

目标AI必须能实际读取本机文件。支持文件访问但无原生Skill安装入口时，可提供SKILL.md及其引用资源作为指令；没有本地读取能力的入口会拒绝售后处理。不同AI产品的安装方式及本地读取能力需在具体客户端验证，不承诺普通云聊天自动读取电脑。

检查器只需Python标准库，可使用系统已有Python；不自动安装依赖。没有Python时按读取契约验证。检查器不联网、不pull、不修改业务文件，也不验证私有库访问授权。

本版Skill为v0.1，已获老板批准公开发布；远端状态以实际Git核验为准。配套私有资料需包含DATASET.json，可使用Rules/Cases v0.1.1；本Skill版本与业务资料版本独立。平台实际验收状态以本次交付记录为准。公开分发时只发布此项目，不包含上级目录的业务资料和私有测试证据。
