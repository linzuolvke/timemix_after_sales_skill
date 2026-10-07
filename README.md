# TimeMix 售后 Skill

当前版本：v0.2.1，配合Cases的新目录格式（schema_version 2）使用。

帮助 TimeMix 舞蹈室处理退款、转卡、停卡、延期、预约扣课、体验券和私教等售后问题。先查本机现行规则，必要时参考历史案例，给出处理方案和可以直接发给客户的微信回复。

## 安装和使用

在支持自定义 Skill、能读取本机文件的 AI 工具里输入：

> 请从 https://github.com/linzuolvke/timemix_after_sales_skill 安装 TimeMix 售后 Skill。先读取 README.md，再读取 timemix-after-sales/SKILL.md，安装整个 timemix-after-sales 文件夹并初始化本机 Rules 和 Cases。复用已有登录；需要 GitHub 授权时告诉我如何完成。最后报告实际安装位置和两个资料库的检查结果。

安装后输入：

> 用 TimeMix 售后 Skill 处理这个问题：[客户情况、课卡、诉求、聊天内容]

安装入口是 [timemix-after-sales/SKILL.md](timemix-after-sales/SKILL.md)。整个技能目录须一起安装，不能只复制一份 SKILL.md。安装后核对实际安装目录里的 `SKILL.md`、`scripts/init_data.py`、`scripts/check_data.py` 和 `references/data-contract.md`；发现旧版或缺文件时重新安装完整目录。不同 AI 工具的安装入口可能不同；助手应先确认本机工具是否能加载 Skill、读取本地资料。

## 资料从哪里来

Skill 公开，经营规则和客户案例私有。两个固定地址不需要使用者重复提供：

| 资料 | 仓库 | 内容 |
|---|---|---|
| Rules | https://github.com/linzuolvke/timemix_rules | 当前有效经营规则 |
| Cases | https://github.com/linzuolvke/timemix_cases | 历史真实事件、聊天文字和最终结果 |

本机默认放置位置：

- macOS：`~/Documents/Obsidian/TimeMix/`
- Windows：系统实际“文档”目录下的 `timemix/TimeMixData/`，不固定盘符

根目录内分别是 `timemix_rules/` 和 `timemix_cases/`。已有其他位置时，告诉助手实际路径即可。

首次使用时检查本机资料，缺哪个库就下载哪个库；首次只下载最新提交，避免拉取旧截图历史。已有目录保留。资料无法实际读取或检查不通过时，暂停售后判断。

## 必要条件和登录

日常使用需要 AI 能读取电脑上的文件。普通网页聊天不能默认获得这项能力。

首次下载或更新需要网络、Git 和两个私有仓库的读取权限。优先复用本机已有的 GitHub 登录；若未登录，助手引导完成一次 GitHub 官方授权。Skill 不附带私钥或令牌。

Windows 常用 Git Credential Manager（GCM）完成并保存 Git 登录。PTY 是让助手运行交互登录的终端方式：WorkBuddy 曾使用它完成授权，但它不是统一必装依赖，也不要求每台电脑安装 pywinpty。无法在助手里交互登录时，可在本机终端完成一次登录，再由助手继续下载。

随附初始化和检查脚本使用 Python 3 标准库，没有第三方 Python 依赖。Windows 使用已有的 `python`、`py -3` 或本机解释器路径；macOS 使用已有的 Python 3。没有 Python 时，助手可按[资料读取契约](timemix-after-sales/references/data-contract.md)完成等效检查；不能静默安装额外环境。

## 怎样处理售后

1. 读取当前问题涉及的 Rules，找出缺少的信息
2. 规则不足或需要比较实际处理方式时，查询相关 Cases
3. 分清现行规则、历史特例、已作出的承诺和未知事实
4. 输出处理方案、计算依据及客户回复；需老板决定的事项明确交给老板

历史案例不自动成为现行规则；店长已实际作出的承诺按已确认口径履行。售后处理只分析和拟回复，不自动操作后台、发送消息或改写资料。

## 更新和维护

日常使用不自动更新。需要同步时输入“更新 TimeMix 的 Rules 和 Cases”，助手核对仓库来源、保护本机改动、更新后重新检查。

- 经营口径改变：维护 Rules 的现行规则、索引和变更记录
- 已处理结束的新事件：维护 Cases 的案例和聊天 Markdown；未知结果先留待确认；每案使用case.md和有实际资料才建立的records.md，原图和完整AI讨论留本机Wiki
- AI 工作流程或回复风格改变：修改 SKILL.md

版本安装包见 [Releases](https://github.com/linzuolvke/timemix_after_sales_skill/releases)。维护者的自动检查位于 `tests/`；通过检查不等于老板已审核案例内容。

检查器只检查本机资料；输出`remote_latest_verified: false`表示没有联网核对远端版本，不表示资料损坏。

发布ZIP内附README.md和SHA256SUMS.txt，后者用于核对包内文件；Release另附SHA256SUMS.txt用于核对ZIP本身。

旧版Cases更新后由新版检查器核查。安装新版Skill不会自动更新已有Cases；明确输入“更新 TimeMix 的 Rules 和 Cases”后才同步。旧库或本地有改动时保护文件并报告，不覆盖。
