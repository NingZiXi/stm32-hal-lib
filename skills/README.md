# 技能

这里存放与组件库配套的可复用开发技能。每个技能同时维护独立仓库，并以 Git 子模块固定版本后随 `stm32-hal-lib` 一起分发。

| 技能 | 独立仓库 | 用途 |
|---|---|---|
| [stm32-app-main](stm32-app-main/) | [GitHub](https://github.com/NingZiXi/stm32-app-main) / [Gitee](https://gitee.com/nzxhg/stm32-app-main) | STM32CubeMX + CMake 的 `main/` 应用结构、stm_log v3 和 RTT 接入 |

更新技能时先提交独立仓库，再更新本目录中的子模块指针，并在总仓库提交固定版本。
