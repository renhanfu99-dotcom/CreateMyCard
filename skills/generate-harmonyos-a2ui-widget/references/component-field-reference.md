# 扩展组件字段参考

## 目录

1. 使用说明
2. 布局组件
3. 展示组件
4. 输入与选择组件
5. 条件组件
6. 自定义扩展组件
7. 组件选择建议

## 1. 使用说明

- 下表只列组件专有字段。所有组件共享的 `id`、`component`、`styles`、`accessibility`、`onClick`、`onAppear` 见 [组件通用字段与样式](common-fields-and-styles.md)。
- “动态”表示字段可使用字面量、DataModel 路径绑定或符合类型的表达式。
- 表格中的“默认值”来自当前文档或渲染器实现；不需要覆盖默认行为时可以省略。
- 标记为“样式”的字段必须放入 `styles`。
- 当前原生扩展组件使用不带 `Extended.` 的名称。只有本文件明确写为 `Extended.*` 的自定义组件保留前缀。

## 2. 布局组件

### 2.1 `Column`

纵向排列子组件，适合作为桌面卡片根布局。

| 顶层字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `children` | ChildList | 无 | 静态子组件 id 数组或模板列表 |
| `itemMargin` | number|string | `8` | 相邻子组件间距 |
| `justifyContent` | string | `start` | 主轴排列：`start`、`center`、`end`、`spaceAround`、`spaceBetween`、`spaceEvenly` |
| `alignItems` | string | `start` | 交叉轴排列：`start`、`center`、`end` |

```json
{"id":"root","component":"Column","children":["header","body"],"itemMargin":12,"alignItems":"start","styles":{"width":"100%","padding":16}}
```

### 2.2 `Row`

横向排列子组件。

| 顶层字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `children` | ChildList | 无 | 静态子组件 id 数组或模板列表 |
| `itemMargin` | number|string | `16` | 相邻子组件间距 |
| `justifyContent` | string | `start` | `start`、`center`、`end`、`spaceAround`、`spaceBetween`、`spaceEvenly` |
| `alignItems` | string | `center` | `top`、`center`、`bottom` |
| `wrap` | string | `noWrap` | `noWrap`、`wrap` |

桌面卡片默认使用 `noWrap`，并为可能变长的文本设置宽度约束和省略号。

### 2.3 `List`

滚动列表。桌面卡片应限制列表高度和数据量。

| 顶层字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `children` | ChildList | 无 | 推荐使用模板列表 |
| `space` | number|string | `0` | 列表项间距 |
| `listDirection` | string | `vertical` | `vertical`、`horizontal` |
| `scrollBar` | string | `auto` | `off`、`auto`、`on` |
| `nestedScroll` | object | `selfOnly` | 前向和后向嵌套滚动策略 |
| `onReachStart` | EventHandler[] | 无 | 到达起始位置 |
| `onReachEnd` | EventHandler[] | 无 | 到达末尾位置 |

`nestedScroll`：

```json
{
  "nestedScroll": {
    "scrollForward": "selfOnly",
    "scrollBackward": "selfOnly"
  }
}
```

策略值：`selfFirst`、`parentFirst`、`paraller`、`selfOnly`。

注意 `paraller` 是当前协议文档与 Schema 中的实际拼写。不要擅自改成通常的英文单词 `parallel`。

### 2.4 `Grid`

网格布局。

| 顶层字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `children` | ChildList | 无 | 静态或模板子组件 |
| `columnsTemplate` | string | `"1fr"` | 列轨道，例如 `"1fr 1fr"` |
| `rowsTemplate` | string | `"1fr"` | 行轨道 |
| `columnsGap` | number|string | `0` | 列间距，必须非负 |
| `rowsGap` | number|string | `0` | 行间距，必须非负 |

不要使用 CSS 的 `repeat(2, 1fr)`，改为 `"1fr 1fr"`。

### 2.5 `Stack`

层叠子组件。

| 顶层字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `children` | string[] | 无 | 按顺序层叠的子组件 id |
| `alignContent` | string | `center` | `topStart`、`top`、`topEnd`、`start`、`center`、`end`、`bottomStart`、`bottom`、`bottomEnd` |

仅在徽标覆盖、背景叠加等确实需要层叠的场景使用。

## 3. 展示组件

### 3.1 `Text`

| 顶层字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `content` | DynamicString | 是 | 显示文本 |

专有样式：

| `styles` 字段 | 类型 | 默认值或枚举 |
|---|---|---|
| `fontColor` | string | 默认约 `#E5000000` |
| `fontSize` | number | 默认 `16`，使用数值 |
| `fontWeight` | string|number | 默认 `400` |
| `maxLines` | number | 最大行数 |
| `minFontSize` | number | 自适应最小字号 |
| `maxFontSize` | number | 自适应最大字号 |
| `textOverflow` | string | `none`、`clip`、`ellipsis`、`marquee`；默认 `clip` |
| `textAlign` | string | 文本对齐方式 |
| `wordBreak` | string | `normal`、`breakAll`、`breakWord`、`hyphenation`；默认 `breakWord` |
| `decoration` | object | 文本装饰 |

`decoration` 可包含 `type`、`color`、`style`、`thicknessScale`。

```json
{"id":"title","component":"Text","content":{"path":"/title"},"styles":{"fontSize":16,"fontWeight":600,"maxLines":1,"textOverflow":"ellipsis"}}
```

### 3.2 `Image`

| 顶层字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `src` | DynamicString | 是 | 图片资源、URI 或绑定路径 |

专有样式：

| `styles` 字段 | 类型 | 默认值或枚举 |
|---|---|---|
| `objectFit` | string | 默认 `cover`；支持 `contain`、`cover`、`auto`、`fill`、`scaleDown`、`none`、九宫格方位值、`matrix` |
| `aspectRatio` | number | 宽高比 |

九宫格方位值：`topStart`、`top`、`topEnd`、`start`、`center`、`end`、`bottomStart`、`bottom`、`bottomEnd`。

### 3.3 `Divider`

无组件专有顶层字段。

| `styles` 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `vertical` | boolean | `false` | 是否为竖分割线 |
| `strokeWidth` | number|string | `"1px"` | 线宽 |
| `color` | string | `#33182431` | 线颜色 |

### 3.4 `Progress`

| 顶层字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `value` | DynamicNumber | `0` | 当前进度 |
| `total` | DynamicNumber | `100` | 总量，须大于 0 |

| `styles` 字段 | 类型 | 默认值或枚举 |
|---|---|---|
| `color` | string | 进度色 |
| `type` | string | `linear`、`ring`、`eclipse`、`scaleRing`、`capsule`；默认 `linear` |

### 3.5 `Button`

| 顶层字段 | 类型 | 必填 | 默认值或说明 |
|---|---|---:|---|
| `label` | DynamicString | 是 | 按钮文本 |
| `enabled` | DynamicBoolean | 否 | 默认 `true` |
| `action` | object | 否 | 目录动作；只有已知动作契约时生成 |

专有样式：`fontSize`、`fontWeight`、`maxFontSize`、`fontScaleMode`、`minFontScale`、`maxFontScale`。

`fontScaleMode` 可用 `followSystem`、`custom`。点击行为优先使用协议事件结构，不能把标准组件的 `child` 写法套到扩展 `Button`。

## 4. 输入与选择组件

普通桌面卡片尽量减少输入控件。仅在目标交互明确且端侧事件闭环已经定义时使用。

### 4.1 `TextInput`

| 顶层字段 | 类型 | 必填 | 默认值或说明 |
|---|---|---:|---|
| `text` | DynamicString | 否 | 当前文本，可双向同步绑定 |
| `placeholder` | DynamicString | 否 | 占位文本 |
| `enabled` | DynamicBoolean | 否 | 默认 `true` |
| `maxLength` | DynamicNumber | 否 | 最大字符数 |
| `type` | string | 是 | 输入类型 |
| `onChange` | EventHandler[] | 否 | 文本变化 |

`type` 可用：`normal`、`number`、`phoneNumber`、`email`、`password`、`numberPassword`、`userName`、`newPassword`、`numberDecimal`、`url`。

常见专有样式：`fontColor`、`fontSize`、`fontWeight`、`placeholderColor`、`placeholderFont`、`textAlign`、`caretColor`、`maxLines`、`inputFilter`。

### 4.2 `Toggle`

| 顶层字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `label` | DynamicString | 无 | 可选标签 |
| `isOn` | DynamicBoolean | `false` | 开关状态 |
| `enabled` | DynamicBoolean | `true` | 是否可操作 |
| `onChange` | EventHandler[] | 无 | 状态变化 |

专有样式：`selectedColor`、`unSelectedColor`、`switchPointColor`。

注意当前实现中 `unSelectedColor` 的大小写与 `Checkbox` 的 `unselectedColor` 不同，不要统一改名。

### 4.3 `Radio`

| 顶层字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `value` | DynamicString | 是 | 单选项值 |
| `group` | DynamicString | 否 | 分组名 |
| `checked` | DynamicBoolean | 否 | 是否选中 |
| `indicatorType` | DynamicString | 否 | 指示器样式，例如勾选或圆点 |
| `onChange` | EventHandler[] | 否 | 选中状态变化 |

专有样式：`checkedBackgroundColor`、`uncheckedBorderColor`、`indicatorColor`。

### 4.4 `Checkbox`

| 顶层字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `label` | DynamicString | 无 | 显示标签 |
| `group` | DynamicString | 无 | 分组名 |
| `select` | DynamicBoolean | `false` | 是否选中 |
| `onChange` | EventHandler[] | 无 | 选中状态变化 |

专有样式：

- `selectedColor`
- `unselectedColor`
- `shape`
- `mark`：可包含 `strokeColor`、`size`、`strokeWidth`

旧文档或其他组件体系可能使用 `value` 表示状态；当前原生扩展 `Checkbox` 使用 `select`。

### 4.5 `CheckboxGroup`

| 顶层字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `group` | DynamicString | 无 | 要控制的复选框分组 |
| `selectAll` | DynamicBoolean | `false` | 全选状态 |
| `onChange` | EventHandler[] | 无 | 分组选中项变化 |

专有样式：`selectedColor`、`unselectedColor`、`shape`、`mark`。`mark` 结构与 `Checkbox` 相同。

## 5. 条件组件

### 5.1 `If`

`If` 是虚拟组件，不渲染实体节点。

| 顶层字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `condition` | DynamicBoolean 或表达式 | 是 | 条件 |
| `childrenIf` | string[] | 是 | 条件为真时的组件 id |
| `childrenElse` | string[] | 建议是 | 条件为假时的组件 id |

```json
{"id":"stateBranch","component":"If","condition":"{{ $__DataModel.meta.state == 'ready' }}","childrenIf":["content"],"childrenElse":["empty"]}
```

## 6. 自定义扩展组件

这些组件保留 `Extended.` 前缀。普通桌面卡片只有在需求明确时才使用。

### 6.1 `Extended.Select`

| 顶层字段 | 类型 | 说明 |
|---|---|---|
| `options` | object[] | 选项；每项至少含 `value`，可含 `icon` |
| `selected` | DynamicNumber | 选中索引，默认 `-1` |
| `value` | DynamicString | 当前显示值 |
| `onChange` | EventHandler[] | 选择变化；当前实现向事件系统派发 `onChange` |

可配置字段包括：`font`、`fontColor`、`selectedOptionBgColor`、`selectedOptionFont`、`selectedOptionFontColor`、`optionBgColor`、`optionFont`、`optionFontColor`、`space`、`arrowPosition`、`menuAlign`、`optionWidth`、`optionHeight`、`menuBackgroundColor`、`divider`。

`arrowPosition` 可用 `START`、`END`；`menuAlign` 可用 `START`、`CENTER`、`END` 或对齐对象。

### 6.2 `Extended.Navigation`

| 顶层字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `children` | string[] | 是 | 页面组件 id |
| `currentIndex` | DynamicNumber | 是 | 当前页面索引 |
| `title` | DynamicString | 是 | 导航标题 |

常用专有样式：`backgroundColor`。

### 6.3 `Extended.Tabs`

| 顶层字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `children` | ChildList | 无 | 通常引用 `Extended.TabContent` |
| `barPosition` | string | `start` | `start`、`end` |
| `vertical` | DynamicBoolean | `false` | 是否纵向 |
| `scrollable` | DynamicBoolean | 无 | 页签栏是否可滚动 |
| `tabIndex` | DynamicNumber | `0` | 当前索引 |
| `onChange` | EventHandler[] | 无 | 页签切换 |

### 6.4 `Extended.TabContent`

| 顶层字段 | 类型 | 说明 |
|---|---|---|
| `title` | DynamicString | 页签标题 |
| `icon` | DynamicString | 默认图标 |
| `selectedSrc` | DynamicString | 选中图标 |
| `tabType` | string | `capsule`、`underline` |
| `child` 或 `children` | string|string[] | 页面内容 |

专有样式：`selectColor`、`unselectedColor`、`defaultBackgroundColor`、`selectBackgroundColor`、`defaultBorderColor`、`selectBorderColor`、`fontSize`、`fontWeight`、`iconSize`、`space`。

### 6.5 `Extended.Web`

| 顶层字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `url` | DynamicString | 是 | 网页地址 |

桌面卡片中不要嵌入网页；该组件更适合完整页面场景。

## 7. 组件选择建议

| 需求 | 优先组件 |
|---|---|
| 标题、摘要、状态 | `Text` |
| 天气图标、头像、缩略图 | `Image` |
| 纵向信息区 | `Column` |
| 指标与图标并排 | `Row` |
| 少量动态待办 | `List` + 模板 |
| 固定二维指标 | `Grid` |
| 完成度 | `Progress` |
| 条件空态 | `If` |
| 明确命令入口 | `Button` |

生成前只读取实际要用的组件章节，并逐项核对：

1. 字段是否位于正确层级；
2. 类型是否允许动态绑定；
3. 枚举拼写是否精确；
4. 所有子组件 id 是否存在；
5. 所有路径绑定是否有初始数据。
