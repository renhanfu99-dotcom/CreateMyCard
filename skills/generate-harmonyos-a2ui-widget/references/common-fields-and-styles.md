# 组件通用字段与样式

## 目录

1. 组件描述符结构
2. 动态值
3. 子组件引用
4. 通用样式
5. 无障碍属性
6. 通用事件
7. 事件处理步骤
8. 生成约束

## 1. 组件描述符结构

鸿蒙扩展组件描述符的通用结构如下：

```json
{
  "id": "title",
  "component": "Text",
  "styles": {
    "width": "100%",
    "padding": 12
  },
  "accessibility": {
    "label": "卡片标题",
    "description": "显示当前卡片主题"
  },
  "onClick": [
    {
      "call": "openDetail",
      "args": {
        "source": "widget"
      }
    }
  ],
  "onAppear": [
    {
      "call": "recordExposure"
    }
  ]
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `id` | string | 是 | Surface 内唯一且稳定的组件标识 |
| `component` | string | 是 | 渲染器已注册的组件类型，不允许动态绑定 |
| `styles` | object | 否 | 通用样式和组件专有样式的容器 |
| `accessibility` | object | 否 | 无障碍标签和描述 |
| `onClick` | EventHandler[] | 否 | 点击事件处理步骤 |
| `onAppear` | EventHandler[] | 否 | 组件出现事件处理步骤 |

部分组件还支持 `onChange`、`onReachStart`、`onReachEnd`。事件是否可用以组件字段参考为准，不要把它们无条件添加到所有组件。

## 2. 动态值

组件字段可能接受以下三类值。必须先查看该字段声明是否支持动态值。

### 2.1 字面量

```json
{"content":"通勤日常"}
```

### 2.2 DataModel 路径绑定

```json
{"content":{"path":"/weather/temperatureLabel"}}
```

路径使用 RFC 6901 JSON Pointer。字符串、数值和布尔字段分别绑定到相同类型的数据。

### 2.3 表达式

```json
{"content":"{{ $__DataModel.tasks.remainingCount + ' 项待办' }}"}
```

表达式仍写在 JSON 字符串中，运行结果必须符合目标字段类型。`id` 和 `component` 不允许使用路径绑定或表达式。

常见动态类型：

| 类型 | 可接受值 |
|---|---|
| `DynamicString` | 字符串、`{"path":"/..."}`、返回字符串的函数调用或表达式 |
| `DynamicNumber` | 数值、`{"path":"/..."}`、返回数值的函数调用或表达式 |
| `DynamicBoolean` | 布尔值、`{"path":"/..."}`、返回布尔值的函数调用或表达式 |

不要仅因为值来自 DataModel，就假设任意字段都支持动态绑定。

## 3. 子组件引用

### 3.1 静态子组件

```json
{"children":["header","body","footer"]}
```

`children` 是组件 id 数组。所有 id 必须已定义，不能在数组中内联组件对象。

只接收单个子组件的字段使用字符串 id：

```json
{"child":"content"}
```

是否支持 `child` 或 `children` 由具体组件决定。

### 3.2 模板列表

```json
{
  "children": {
    "componentId": "taskRow",
    "path": "/tasks/items",
    "itemVar": "$item",
    "indexVar": "$index"
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `componentId` | string | 是 | 列表项模板根组件 id |
| `path` | string | 是 | 指向数组的 DataModel 路径 |
| `itemVar` | string | 否 | 当前项变量名；默认按运行时约定使用 `$item` |
| `indexVar` | string | 否 | 当前索引变量名；默认按运行时约定使用 `$index` |

模板组件只定义一次。不要为初始数组中的每个元素复制一套组件。

## 4. 通用样式

以下字段均放入 `styles`。组件专有样式也与它们放在同一个 `styles` 对象中。

### 4.1 尺寸

| 字段 | 类型 | 说明 |
|---|---|---|
| `width` | number|string | 宽度；可用数值、尺寸字符串或布局枚举 |
| `height` | number|string | 高度；可用数值、尺寸字符串或布局枚举 |
| `constraintSize` | object | 最小和最大尺寸约束 |

`width`、`height` 支持：

- 数值：按当前渲染器的尺寸规则处理，常用于 vp 尺寸；
- 字符串尺寸：`"24vp"`、`"50%"`；
- 布局枚举：`matchParent`、`wrapContent`、`fixAtIdealSize`。

`constraintSize`：

```json
{
  "constraintSize": {
    "minWidth": 80,
    "maxWidth": "100%",
    "minHeight": 32,
    "maxHeight": 120
  }
}
```

### 4.2 外边距与内边距

`margin`、`padding` 可为数值、尺寸字符串或四边对象：

```json
{
  "margin": {"top":8,"right":12,"bottom":8,"left":12},
  "padding": 12
}
```

四边字段为 `top`、`right`、`bottom`、`left`。不要使用 CSS 简写数组或 `"8 12"` 字符串。

### 4.3 边框与圆角

| 字段 | 类型 | 说明 |
|---|---|---|
| `borderRadius` | number|string|object | 统一圆角或四角圆角 |
| `borderWidth` | number|string|object | 边框宽度 |
| `borderColor` | string|object | 边框颜色 |

四角圆角：

```json
{
  "borderRadius": {
    "topLeft": 12,
    "topRight": 12,
    "bottomLeft": 8,
    "bottomRight": 8
  }
}
```

### 4.4 背景

| 字段 | 类型 | 说明 |
|---|---|---|
| `backgroundColor` | string | `#RRGGBB` 或 `#AARRGGBB` |
| `backgroundImage` | string | 背景图片资源或地址 |
| `backgroundImageSizeWithStyle` | string|object | 图片缩放方式或显式尺寸 |
| `linearGradient` | object | 线性渐变配置 |

`backgroundImageSizeWithStyle` 可用 `cover`、`contain`、`auto`、`fill`，或：

```json
{"backgroundImageSizeWithStyle":{"width":"100%","height":"100%"}}
```

`linearGradient` 常用结构：

```json
{
  "linearGradient": {
    "angle": 90,
    "direction": "Right",
    "colors": ["#FFFFFFFF","#FFF2F5FA"],
    "stops": [0,1],
    "repeating": false
  }
}
```

`direction` 可用 `Left`、`Right`、`Top`、`Bottom`、`LeftTop`、`LeftBottom`、`RightTop`、`RightBottom`、`None`。

### 4.5 布局参与属性

| 字段 | 类型 | 说明 |
|---|---|---|
| `layoutWeight` | number | 在父布局剩余空间中的权重 |
| `flexShrink` | number | 空间不足时的收缩系数 |

不要用 `layoutWeight` 代替固定尺寸约束。桌面卡片布局应在目标尺寸下保持稳定。

### 4.6 阴影

`shadow` 可使用预设：

`outerDefaultXS`、`outerDefaultSM`、`outerDefaultMD`、`outerDefaultLG`、`outerFloatingSM`、`outerFloatingMD`

也可使用对象：

```json
{
  "shadow": {
    "radius": 8,
    "color": "#33000000",
    "offsetX": 0,
    "offsetY": 2,
    "fill": false,
    "type": "color",
    "style": "outer"
  }
}
```

对象形式的 `radius` 必填。不要为小尺寸卡片堆叠多个强阴影。

### 4.7 显隐与裁剪

| 字段 | 类型 | 可选值或说明 |
|---|---|---|
| `visibility` | string | `visible`、`hidden`、`none` |
| `clip` | boolean | 是否裁剪超出组件边界的内容 |

- `hidden`：不可见但保留布局空间。
- `none`：不可见且不占布局空间。
- 圆角图片通常同时设置 `borderRadius` 和 `clip: true`。

## 5. 无障碍属性

```json
{
  "accessibility": {
    "label": {"path":"/weather/accessibilityLabel"},
    "description": "点击查看天气详情"
  }
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `label` | DynamicString | 朗读名称 |
| `description` | DynamicString | 补充用途或状态 |

为无文本图标、图片按钮、关键指标和可交互控件提供 `label`。纯装饰组件不要添加重复且无意义的朗读内容。

## 6. 通用事件

渲染器能够识别的事件名包括：

- `onClick`
- `onAppear`
- `onChange`
- `onReachStart`
- `onReachEnd`

其中 `onClick`、`onAppear` 属于协议通用字段；其余事件只在对应组件上使用：

| 事件 | 常见组件 |
|---|---|
| `onChange` | `TextInput`、`Toggle`、`Radio`、`Checkbox`、`CheckboxGroup`、`Extended.Tabs`、`Extended.Select` |
| `onReachStart` | `List` |
| `onReachEnd` | `List` |

事件字段值是处理步骤数组，不是单个字符串：

```json
{
  "onClick": [
    {"call":"openTaskList","args":{"source":"desktopWidget"}}
  ]
}
```

## 7. 事件处理步骤

单个 EventHandler 步骤：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `call` | string | 是 | 要调用的函数或动作名 |
| `args` | object | 否 | 调用参数 |
| `condition` | string | 否 | 执行条件表达式 |
| `as` | string | 否 | 保存返回结果的变量名 |

```json
{
  "onClick": [
    {
      "call": "getTaskDetail",
      "args": {"taskId":"{{ $item.id }}"},
      "condition": "{{ !$item.done }}",
      "as": "taskDetail"
    },
    {
      "call": "openTaskDetail",
      "args": {"detail":"{{ taskDetail }}"}
    }
  ]
}
```

只有端侧或目录中已注册的函数才能被调用。没有函数目录信息时，不得虚构 `call` 名称；可省略事件，或明确将动作名作为待接入占位契约。

## 8. 生成约束

- 先确定字段属于组件顶层还是 `styles`，再生成 JSON。
- 通用样式必须放入 `styles`，不要写成组件顶层字段。
- 组件专有布局字段通常位于顶层，例如 `Row.justifyContent`；以组件字段参考为准。
- 不要输出文档和源码均未声明的字段。
- 不要因为多个组件字段同名，就假设它们的枚举和默认值相同。
- 动态值的结果类型必须与目标字段类型一致。
- 省略可选字段通常优于生成无依据的默认值。
- 当文档、Schema 与当前渲染器实现冲突时，以当前渲染器实际解析和注册行为为准。
