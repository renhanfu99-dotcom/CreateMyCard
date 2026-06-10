# 协议与生成规则

## 目录

1. 消息流
2. 组件图
3. DataModel 与数据绑定
4. 表达式
5. 动态列表
6. 流式处理与数据更新
7. 桌面卡片设计规则
8. 错误检查清单

## 1. 消息流

每一行必须是一个完整 JSON 对象，包含 `version: "v0.9"`，且只能包含一种消息体。

服务端到端侧支持以下消息：

| 消息 | 必填字段 | 作用 |
|---|---|---|
| `createSurface` | `surfaceId`、`catalogId` | 创建渲染作用域 |
| `updateComponents` | `surfaceId`、`components` | 新增或更新扁平组件定义 |
| `updateDataModel` | `surfaceId` | 新增、更新或删除数据 |
| `deleteSurface` | `surfaceId` | 销毁渲染作用域 |

规则：

- 第一条消息必须是 `createSurface`。
- 整条消息流中的 `surfaceId` 必须一致。
- 本 Skill 描述的扩展组件使用 `ohos.a2ui.extended.catalog`。
- 初始化数据时，将 `updateDataModel.path` 设置为 `/`。
- 后续 `updateDataModel` 可以只更新子树，例如 `/weather`。
- 省略 `value` 表示删除 `path` 对应的数据，不得意外省略。
- `updateComponents` 使用合并更新语义，后续消息可以按 id 替换单个组件定义。

## 2. 组件图

组件的通用字段、动态值、`styles`、无障碍属性和事件结构见 [组件通用字段与样式](common-fields-and-styles.md)。组件专有字段见 [扩展组件字段参考](component-field-reference.md)。生成时必须同时遵守通用层和组件专有层定义。

组件使用扁平邻接表：

```json
[
  {"id":"root","component":"Column","children":["header","body"]},
  {"id":"header","component":"Text","content":"通勤日常"},
  {"id":"body","component":"Row","children":["weather","tasks"]}
]
```

硬性规则：

- 每个组件都有唯一且非空的 `id`。
- 每个被引用的子组件 id 都必须在同一个 Surface 中存在。
- 使用 `root` 作为唯一入口组件。
- 不要在 `children` 中内联组件对象。
- 不得形成循环引用或自引用。
- 模板组件与引用它的容器必须位于同一个组件集合。
- 不得把通用样式写到组件顶层，也不得把 `justifyContent` 等组件专有布局字段误放进 `styles`。

## 3. DataModel 与数据绑定

路径使用 RFC 6901 JSON Pointer：

```json
{"path":"/weather/temperatureLabel"}
```

DataModel 应围绕 UI 语义设计：

```json
{
  "title": "通勤日常",
  "weather": {
    "condition": "多云",
    "temperatureC": 24,
    "temperatureLabel": "24°",
    "advice": "早晚微凉"
  },
  "tasks": {
    "remainingCount": 2,
    "summary": "2 项待办",
    "items": [
      {"title":"提交周报","done":false},
      {"title":"预约会议室","done":true}
    ]
  },
  "meta": {
    "updatedAtLabel": "08:30 更新",
    "state": "就绪"
  }
}
```

规则：

- 初始化每个绝对绑定路径。
- 数据类型必须与组件属性要求一致。
- 直接读取数据时使用 `{ "path": "/..." }`。
- 计算或进度组件需要数值时，保留原始数值字段。
- UI 需要本地化文本时，同时提供格式化后的展示字段。
- 不要让展示字段直接绑定操作系统接口的原始返回结构。后续的 DataBindingPlan 应负责把设备数据归一化到该 DataModel。

## 4. 表达式

表达式只在鸿蒙扩展组件目录下可用：

```json
{"content":"{{ $__DataModel.tasks.remainingCount + ' 项待办' }}"}
```

可用变量包括：

- `$__DataModel`
- `$__WindowWidthBreakpoint`：`xs`、`sm`、`md`、`lg`、`xl`
- `$__ColorMode`：`light`、`dark`
- 模板中的 `$item`、`$index`

表达式适用于：

- 短字符串拼接；
- 条件文案；
- 条件颜色或显隐；
- 窄屏与宽屏布局选择。

禁止：

- 在 `id` 或 `component` 中使用表达式；
- 在 `{ "path": ... }` 绑定内部使用表达式；
- 放入超出展示层职责的复杂业务逻辑；
- 假设支持 JavaScript 方法或任意代码执行；
- 使用非标准断点名称。

数值样式属性的表达式结果必须为数值：

```json
{"styles":{"fontSize":"{{ $__WindowWidthBreakpoint == 'xs' ? 14 : 16 }}"}}
```

不需要计算时优先使用直接路径绑定。

## 5. 动态列表

重复数据使用模板对象：

```json
{"id":"taskList","component":"List","children":{"componentId":"taskRow","path":"/tasks/items"},"scrollBar":"off"}
{"id":"taskRow","component":"Row","children":["taskDot","taskTitle"],"itemMargin":8}
{"id":"taskDot","component":"Text","content":"{{ $item.done ? '✓' : '○' }}"}
{"id":"taskTitle","component":"Text","content":"{{ $item.title }}","styles":{"maxLines":1,"textOverflow":"ellipsis"}}
```

规则：

- 模板 `path` 必须指向数组。
- 模板内部可通过 `$item` 表达式读取当前项。
- 模板 id 保持稳定，由渲染器为每个数组元素创建实例。
- 小尺寸卡片应限制可见内容，优先展示摘要和少量列表项，不使用无限滚动区域。

## 6. 流式处理与数据更新

推荐的初始化消息流：

1. 创建 Surface。
2. 发送完整组件骨架。
3. 发送具有代表性的初始数据。

后续刷新示例：

```json
{"version":"v0.9","updateDataModel":{"surfaceId":"commute-daily","path":"/weather","value":{"temperatureLabel":"25°","condition":"晴"}}}
```

普通刷新不要重新发送 `createSurface`。只有数据变化时，不要重建组件。

如果模型按词元流式生成，端侧必须缓存到一个完整 JSON 对象闭合后，再传给 `SurfaceController.onReceive`。

## 7. 桌面卡片设计规则

- 以数秒内能够完成扫读为目标。
- 使用清晰标题、一个主要指标和不超过两个次要区域。
- 只有目标尺寸能保证每列可读时才使用双列布局。
- 避免在桌面卡片中放置密集控件。
- 待办标题和状态文本使用省略号限制。
- 提供有意义的空态，例如 `今天没有待办`。
- 需求涉及加载态或错误态时，使用 DataModel 状态和预定义组件或 `If` 分支表达。
- 使用中性背景和语义强调色，不得只依赖颜色表达状态。
- 动态文本不得导致组件图发生不可预测的尺寸变化。

## 8. 错误检查清单

当前仓库快照中的校验权威顺序：

1. `genui/src/main` 下的渲染器注册与实现。
2. 单组件文档和单组件渲染 Schema。
3. 聚合 `extended_catalog.json` 仅作辅助参考。

不要将聚合 Schema 作为当前快照中的唯一门禁。它的普通字符串与表达式联合类型，以及 `allOf` 与 `unevaluatedProperties` 的组合，可能拒绝渲染器实际支持的值，或产生 `oneOf` 多重匹配误报。

拒绝或修复以下 DSL：

- 协议版本错误；
- 组件目录错误或混用；
- JSONL 中包含解释文字、注释或 Markdown；
- 一个消息信封中包含多个消息体；
- 缺少 `root`；
- 组件 id 重复；
- `children`、`child`、`trigger`、`content` 存在悬空引用；
- 扩展 `Text` 使用 `text`；
- 扩展 `Image` 使用 `url`；
- 扩展 `Button` 使用 `child`；
- 原生扩展组件错误使用 `Extended.*` 前缀；
- `fontSize` 写成 `"16fp"` 等字符串；
- Grid 使用 `repeat(...)`；
- 响应式 `If` 缺少 `childrenElse`；
- 初始 DataModel 缺少绑定路径的根字段；
- 将数组渲染成固定数量的重复组件，而不是模板列表；
- 虚构查询接口或写入真实用户隐私数据。
