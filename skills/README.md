# 配套应用接入技能

本目录分发独立技能仓库的固定 Git 子模块版本，不是总仓库的常驻 Agent 指令目录。维护本仓库从 [AGENTS.md](../AGENTS.md) 开始，技能维护与引用更新遵循 [CONTRIBUTING.md](../CONTRIBUTING.md)。

| 技能 | 独立仓库 | 当前分发范围 |
| --- | --- | --- |
| [stm32-app-main](stm32-app-main/README.md) | [GitHub](https://github.com/NingZiXi/stm32-app-main) / [Gitee](https://gitee.com/nzxhg/stm32-app-main) | CubeMX1 CMake 工程的独立 main/、裸机/FreeRTOS 入口及 stm_log v3.0.0 UART/RTT 接入 |

## 使用与按需读取

只有将业务入口和日志接入外部 CubeMX 工程时才使用此技能；修改总仓库文档、CI 或组件实现不需要执行它。当前分发版本仅声明 CubeMX1 的 `.ioc` 路径，不能把远端新版或其他位置安装的 skill 能力当成本目录已有能力。

Agent 是否自动发现技能取决于客户端。需要安装时将技能**整个目录**复制到客户端支持的技能目录，保持 `SKILL.md`、references 和 assets 的相对路径；当前目录存在不意味着它已被启用。使用前确认实际加载的位置和版本。

- [README](stm32-app-main/README.md)：适用范围、安装与使用。
- [SKILL.md](stm32-app-main/SKILL.md)：任务流程与必要阅读条件。
- references：按当前接入、日志后端、构建或注释任务读取。
- assets：选择并适配模板，不把所有模板加载成常驻指令。

目标消费工程的指令、实际生成的接口和已选依赖决定适配方式；本仓库 AGENTS.md 不随技能自动传播到外部工程。模板的应用注释偏好不适用于整个组件库。

## 依赖与分发版本

技能通过 FetchContent 固定 stm_log v3.0.0；总仓库 `lib/stm_log` 的实际版本见[组件表](../README.md)。两条接入路径分别维护；总仓库选择 v2 时仍包含 HAL 依赖，不能用该说明替代技能的 v3 回调接口。执行技能不会自动更新本仓库子模块，也不应在同一工程创建两个同名 target。

技能子模块的修改在其独立仓库验证、提交和发布后，再更新总仓库 gitlink。自动组件 tag 同步任务仅处理 lib/，不更新本目录。实际分发提交以总仓库 gitlink 为准。
