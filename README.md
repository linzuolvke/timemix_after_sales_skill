# TimeMix售后Skill

公开Skill位于`timemix-after-sales/`，将整个文件夹导入支持自定义Skill的工具。Rules和Cases独立保持私有，本公开项目不包含经营资料或访问密钥。

当前版本为 **v0.1.2**，请使用[v0.1.2安装包](https://github.com/linzuolvke/timemix_after_sales_skill/releases/tag/v0.1.2)。v0.1.1不包含本次Windows凭据/原件字节修复；旧v0.1没有初始化功能。

## 给安装工具的入口说明

用户只提供本公开仓库地址时，安装工具应先读取本页，再完整读取[技能入口](timemix-after-sales/SKILL.md)，按当前客户端支持方式安装整个`timemix-after-sales/`文件夹。不要把仓库根目录当作技能目录，也不要只导入SKILL.md。

两个依赖地址已经固定，无需向用户索取：

- Rules（private）：https://github.com/linzuolvke/timemix_rules.git → `timemix_rules/`
- Cases（private）：https://github.com/linzuolvke/timemix_cases.git → `timemix_cases/`

安装完成后实际读取已安装的`timemix-after-sales/SKILL.md`并核对版本、两个地址和以下随附文件：

- `scripts/init_data.py`：首次补齐缺失资料库
- `scripts/check_data.py`：只读完整性检查
- `references/data-contract.md`：无Python时的等效检查契约

旧版v0.1没有自动初始化功能。不能默认使用旧Release安装包，也不能只根据ZIP文件名认定版本；以已安装SKILL正文及随附文件为准。公开主分支、Release包、已安装副本可能不同，必须确认实际安装的版本具备本流程。缺文件或缺地址时报告“旧版或安装不完整”并核对来源，不让用户重复提供资料地址。

确认平台已加载Skill后，调用其初始化流程，并分别报告“技能安装/识别”和“资料下载/校验”的实际结果。GitHub私有库授权可能需要用户完成官方身份步骤；不能把浏览器已登录等同于Git凭据可用。

## 首次使用

首次调用Skill时自动检查本机资料。缺库时调用随附初始化工具，下载获授权的私有库；已有库保留，随后完整校验。安装Skill本身是否能立即运行初始化取决于客户端，不能承诺所有平台都有安装钩子。

资料根目录结构：

```text
资料根目录/
├── timemix_rules/
└── timemix_cases/
```

macOS默认：当前用户`Documents/Obsidian/TimeMix/`。
Windows默认：系统实际文档目录下`timemix/TimeMixData/`，兼容目录重定向。
其他位置可通过`TIMEMIX_DATA_ROOT`或明确路径指定。

首次下载需Git、网络和两个私有库的读取权限。复用已有登录；未登录时引导用户完成GitHub官方授权，不将私钥或令牌写入Skill或聊天。检查/初始化脚本仅使用Python标准库；Windows可按本机环境使用Python 3的`python`、`py -3`或解释器绝对路径。缺命令不等于缺Python；不自动安装依赖。无Python可按SKILL和读取契约完成等效操作，能力不足须明确说明。

## 验证及日常处理

`init_data.py`仅下载缺失的资料库并复验，不覆盖已有目录。失败的暂存目录保留；身份检查、完整资料校验失败均暂停售后处理。

`check_data.py`只读、不联网。验证结构、身份、引用、结案和审核字段及原件哈希，统计待审核案例；不替老板审核内容、不证明远端最新、不验证访问授权。资料版本与Skill版本独立。

目标AI必须能实际读取本机文件，普通云聊天或上传附件不能假定具备此能力。支持本地读取而无原生Skill入口时，可按客户端支持方式提供SKILL.md及引用资源；仍需实际验证能读取和执行。

日常使用不自动pull；用户明确要求更新时才按SKILL中的来源核对、工作区保护和仅快进流程更新并重新校验。

## Windows初始化兼容（v0.1.2）

初始化先做限时访问检查，输出进度，必要时对本次Git命令绕过PortableGit的helper-selector并选择已安装的manager；支持指定Git路径及凭据助手，不修改全局设置。访问默认30秒、下载默认180秒，超时尝试终止本次进程树并保留暂存。原件按字节校验，新库禁用Git换行转换并保存本地配置。

首次授权可能需要用户完成浏览器身份步骤。如果助手环境没有可用交互入口，只请用户在自己的终端完成一次官方GitHub登录，随后由助手下载和校验两库，不要求用户手动clone。不把代理502误报为账号权限问题，不自动绕过代理；按失败原因采取下一步。

参数详见`python3 scripts/init_data.py --help`（Python命令按本机实际情况调整）。
