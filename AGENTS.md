# 在 stm32-hal-lib 中工作

## 仓库边界

- 总仓库维护组件组合、接入文档和集成 CI。`lib/` 中的自有组件及 `skills/stm32-app-main/` 是独立 Git 子模块；修改前检查该子模块的状态、实际提交和局部指令。组件或技能的修改与总仓库 gitlink 更新分别审查。
- `lib/fatfs/` 是第三方源码副本；保留授权信息。`build/`、`.ci-deps/` 和自动获取的 `lib/littlefs/` 不是通用源码编辑入口。
- 本仓库没有根固件工程。`ci/` 是编译、链接和软件测试环境；实际板级 HAL、时钟、引脚、链接脚本与烧录配置属于消费工程。

## 开始任务与按需阅读

先用 `git status -sb`、`git submodule status` 确认本地状态与组合。不要为整理文档而更新组件、覆盖开发提交或同步远端分支。

| 任务 | 继续阅读 |
| --- | --- |
| 使用或介绍组件 | [README.md](README.md)，再读所选组件当前提交的 README 和示例 |
| 修改组件、引用或发布流程 | [CONTRIBUTING.md](CONTRIBUTING.md)，再读目标组件的公开头文件、CMake、实现和相关测试 |
| 开发显示/触摸/LVGL 组件 | [显示开发规范](docs/display-development.md)；具体契约以目标版本头文件为准 |
| 接入显示功能或迁移接口 | [显示接入指南](docs/display-components.md)及选中组件的板级示例 |
| 修改检查脚本或工作流 | [ci/README.md](ci/README.md)、受影响的脚本与 `.github/workflows/` |
| 将业务入口和日志接入外部 CubeMX 工程 | [skills/README.md](skills/README.md)，适用时激活其固定版本的 SKILL.md，再按所选后端读取 reference/asset |

只读当前任务需要的材料。维护总仓库文档或驱动不需要激活应用接入 skill；skill 不向外部工程传播本仓库的目录指令。

## 信息来源与版本

- 固定组合由总仓库提交中的 gitlink 决定；开发时区分 HEAD、暂存区和子模块工作区。`.gitmodules` 决定路径与获取地址。README 表格是这些事实的展示，应同步更新。
- 接口契约查同一提交的公开头文件；构建选项查 CMake，CI 执行步骤查工作流。发现文档、实现或测试不一致时明确指出并修正，不以远端最新 README 覆盖本地版本事实。
- 通用维护政策集中在 CONTRIBUTING，显示领域要求集中在显示开发规范。AGENTS.md 提供阅读入口，不复制整套政策或 API。
- 总仓库的 stm_log gitlink 与应用接入 skill 的 FetchContent 是不同消费路径，按各自实际版本核对 API 和 HAL 依赖，不由其中一条路径推定另一条版本。
- 未发布提交、数字版本 tag、正式 Release 和硬件验收分别描述。临时任务限制不作为永久仓库政策；发布及远端变更按当前任务授权和维护流程执行。

## 验证与交付

总仓库文档或引用修改后运行 `python ci/check_repository.py`；同步脚本或其检查修改后再运行 `python -m unittest discover -s ci -p test_sync_latest_tags.py`。新增 Markdown 纳入链接检查，子模块内部文档在各自仓库单独检查。

组件和 CI 修改按 [ci/README.md](ci/README.md)选择相关检查；不要把文档整理扩展成完整固件构建或板测。该检查器核对暂存区 gitlink 和工作区 HEAD，不证明提交已经推送、存在 Release 或硬件通过。

交付说明修改位置、使用的版本、执行的检查与未验证范围。区分编译、主机/模拟测试、完整固件链接和实板测试；硬件结论须对应具体提交、器件与测试条件。
