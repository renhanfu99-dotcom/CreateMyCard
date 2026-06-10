---
name: generate-harmonyos-a2ui-widget
description: 生成、审查和修复用于 AI 桌面卡片与元服务卡片技术穿刺的鸿蒙 A2UI v0.9 JSONL DSL。当 Agent 需要把用户的自然语言卡片需求转换为可由华为 GenUI/A2UIRender 渲染的 createSurface、updateComponents、updateDataModel 消息时使用，尤其适用于鸿蒙扩展组件、DataModel 动态绑定、模板列表、表达式、自适应布局和流式输出场景。
---

# 生成鸿蒙 A2UI 桌面卡片

生成可直接交给渲染器处理的 A2UI JSONL。当文档与实现不一致时，以当前鸿蒙渲染器源码的实际行为为准。

## 默认目标

- 协议版本固定使用 `v0.9`。
- 桌面卡片默认使用 `catalogId: "ohos.a2ui.extended.catalog"`，除非需求明确指定标准组件目录。
- 只使用渲染器已注册的组件名。扩展组件目录中的原生组件使用不带前缀的名称，例如 `Text`、`Button`、`Column`、`Progress`；不要生成 `Extended.Text` 或 `Extended.Button`。
- 输出格式为 JSONL：每行一个完整 JSON 对象，不得包含 Markdown 代码围栏、注释、解释文字、尾随逗号或跨行的不完整对象。
- 默认只生成 UI DSL 和具有代表性的初始数据。除非需求明确要求，否则不要虚构 `DataBindingPlan`、查询命令、权限、刷新策略或能力标识。

生成 DSL 前先阅读 [协议与生成规则](references/protocol-and-generation-rules.md) 和 [组件通用字段与样式](references/common-fields-and-styles.md)。使用 [扩展组件索引](references/extended-component-catalog.md) 完成选型，再按实际选用的组件读取 [扩展组件字段参考](references/component-field-reference.md) 中对应章节。需要完整消息结构时阅读 [桌面卡片示例](references/widget-examples.jsonl)。

## 执行流程

1. 将用户需求拆解为：
   - 卡片用途；
   - 目标尺寸；
   - 静态文案；
   - 动态字段；
   - 重复集合；
   - 交互行为；
   - 与需求范围匹配的空态、加载态和错误态。
2. 编写组件前先设计稳定的 DataModel。
   - 使用语义明确且不依赖数据源实现的路径，例如 `/weather/temperatureLabel`、`/tasks/items`。
   - 格式可能变化时，将用于展示的字符串与原始值分开保存。
   - 重复内容使用数组。
   - 为 UI 引用的每个路径提供有代表性的初始值。
3. 设计紧凑的组件树。
   - 只定义一个入口根组件，id 固定为 `root`。
   - 使用扁平邻接表，通过 id 引用子组件。
   - 优先使用 `Column`、`Row`、`Text`、`Image`、`Progress`、`List`、`Grid`、`Stack`、`If`。
   - 桌面卡片应便于快速扫读。除非需求明确要求，否则避免导航、表单、网页、标签页和音视频组件。
   - 长文本使用 `maxLines` 和 `textOverflow` 限制。
4. 为每个选用组件核对字段。
   - 先添加必填的 `id` 和 `component`。
   - 区分组件顶层字段与 `styles` 字段，不得凭经验移动属性。
   - 只对声明为动态类型的字段使用路径绑定或表达式。
   - 只使用字段参考中列出的枚举值；无依据时省略可选字段。
   - 交互组件必须核对事件名、EventHandler 数组结构和已注册的 `call`。
5. 按以下顺序输出消息：
   - `createSurface`；
   - 一条或多条 `updateComponents`；
   - 一条初始化 `updateDataModel`。
6. 绑定动态值。
   - 直接读取数据时优先使用 `{ "path": "/..." }`。
   - 仅在短文本拼接、条件文案、颜色模式或断点判断中使用 `{{ ... }}` 表达式。
   - 重复数组使用模板子节点，不要生成固定数量的重复行。
7. 自检所有组件引用、数据路径、字段类型、字段层级和组件目录专属属性。
8. 有输出路径时，将 JSONL 写入文件并执行：

```powershell
python scripts/validate_a2ui_jsonl.py <JSONL文件路径>
```

修复所有错误。警告应作为设计复核项处理。

## 输出约定

用户只要求 DSL 时，仅返回 JSONL，不附加其他文字。

用户同时要求解释时，将解释与原始 JSONL 文件分开，绝不在 JSONL 消息流中混入说明文字。

最小消息结构：

```json
{"version":"v0.9","createSurface":{"surfaceId":"example-widget","catalogId":"ohos.a2ui.extended.catalog","theme":{"primaryColor":"#0A59F7"}}}
{"version":"v0.9","updateComponents":{"surfaceId":"example-widget","components":[{"id":"root","component":"Column","children":["title"]},{"id":"title","component":"Text","content":{"path":"/title"}}]}}
{"version":"v0.9","updateDataModel":{"surfaceId":"example-widget","path":"/","value":{"title":"示例"}}}
```

## 桌面卡片约束

- 每个 Surface 只承载一张逻辑卡片。
- `surfaceId` 使用稳定的短横线命名；组件 id 使用稳定且能表达用途的名称。
- 根组件宽度设置为 `"100%"`；只有已知目标卡片尺寸时才约束高度。
- 通过 `itemMargin`、`space`、`styles.padding` 明确设置间距。
- `fontSize`、`minFontSize`、`maxFontSize` 使用数值，不得写成 `"16fp"`。
- 颜色使用 `#RRGGBB` 或 `#AARRGGBB`。
- 通用尺寸、间距、背景、边框、阴影、显隐和裁剪字段放入 `styles`。
- `accessibility.label` 和 `accessibility.description` 支持动态字符串；只为需要朗读的内容添加。
- 仅图标控件和重要数值摘要应提供无障碍标签。
- 最近一次成功数据的保留策略由 DSL 外部的运行时负责，不要把刷新执行或设备数据访问编码进 A2UI 消息。
- 示例数据不得暴露真实设备隐私，使用明显虚构的数据。

## 修复规则

审查已有 DSL 时：

- 修复扩展组件目录中误用的标准组件属性：
  - `Text.text` 改为 `Text.content`
  - `Image.url` 改为 `Image.src`
  - 标准 `Button.child` 改为扩展 `Button.label`
  - `Row.justify` 改为 `Row.justifyContent`
  - `Row.align` 改为 `Row.alignItems`
- 组件规范要求视觉属性位于 `styles` 时，将属性移入 `styles`。
- 将不存在的组件前缀改为渲染器实际注册的组件名。
- 补齐被引用但未定义的组件，以及绑定路径缺少的初始 DataModel 字段。
- 所有消息必须使用同一个 `surfaceId`。
- 不要为了让错误 DSL 通过而静默切换组件目录。
