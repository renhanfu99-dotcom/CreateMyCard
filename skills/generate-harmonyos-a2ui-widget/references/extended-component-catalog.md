# 鸿蒙扩展组件索引

生成组件前必须先读 [组件通用字段与样式](common-fields-and-styles.md)，再按实际选用的组件读取 [扩展组件字段参考](component-field-reference.md)。本文只用于快速选型和检查组件名称，不代替字段定义。

本文列出生成桌面卡片时最常用的组件。当前渲染器源码注册了以下不带 `Extended.` 前缀的原生扩展组件：

`Button`、`Text`、`TextInput`、`Row`、`Column`、`List`、`Stack`、`Grid`、`Image`、`Divider`、`Toggle`、`Progress`、`Radio`、`Checkbox`、`CheckboxGroup`。

协议还定义了虚拟组件 `If`。自定义扩展组件包括 `Extended.Select`、`Extended.Navigation`、`Extended.Tabs`、`Extended.TabContent`、`Extended.Web`；普通桌面卡片应尽量避免使用。

## 快速选型

| 组件 | 关键字段 | 说明 |
|---|---|---|
| `Column` | `children`、`itemMargin`、`justifyContent`、`alignItems`、`styles` | 用于根布局和纵向分区 |
| `Row` | `children`、`itemMargin`、`justifyContent`、`alignItems`、`wrap`、`styles` | `alignItems` 可用 `top`、`center`、`bottom` |
| `List` | `children`、`space`、`listDirection`、`scrollBar`、`nestedScroll`、`styles` | 明确设置 `scrollBar`；数组使用模板子节点 |
| `Grid` | `children`、`columnsTemplate`、`rowsTemplate`、`columnsGap`、`rowsGap`、`styles` | 使用 `"1fr 1fr"`，不要使用 `repeat()` |
| `Stack` | `children`、`alignContent`、`styles` | 仅在确实需要层叠时使用 |
| `Text` | `content`、`styles` | `content` 支持字面量、路径绑定和表达式 |
| `Image` | `src`、`styles` | `objectFit`、`aspectRatio` 放在 `styles` 内 |
| `Divider` | `styles.vertical`、`styles.strokeWidth`、`styles.color` | Divider 专属属性全部放在 `styles` 内 |
| `Progress` | `value`、`total`、`styles` | `styles.type` 支持 `linear`、`ring`、`eclipse`、`scaleRing`、`capsule` |
| `Button` | `label`、`enabled`、`action`、`styles` | 原生扩展组件名是 `Button` |
| `Toggle` | `isOn`、`label`、`styles` | 仅在卡片确实需要交互时使用 |
| `If` | `condition`、`childrenIf`、`childrenElse` | 虚拟条件组件 |

## 最小示例

```json
{"id":"taskTitle","component":"Text","content":"{{ $item.title }}","styles":{"fontSize":14,"fontColor":"#E6000000","maxLines":1,"textOverflow":"ellipsis","wordBreak":"breakWord"}}
```

```json
{"id":"weatherIcon","component":"Image","src":{"path":"/weather/icon"},"styles":{"width":40,"height":40,"objectFit":"contain","borderRadius":8,"clip":true}}
```

```json
{"id":"progress","component":"Progress","value":{"path":"/tasks/completed"},"total":{"path":"/tasks/total"},"styles":{"width":"100%","height":6,"color":"#0A59F7","type":"capsule"}}
```

## 常见误写

| 错误写法 | 正确写法 |
|---|---|
| `{"component":"Text","text":"..."}` | `{"component":"Text","content":"..."}` |
| `{"component":"Image","url":"..."}` | `{"component":"Image","src":"..."}` |
| `{"component":"Button","child":"labelText"}` | `{"component":"Button","label":"..."}` |
| `{"component":"Row","justify":"spaceBetween"}` | `{"component":"Row","justifyContent":"spaceBetween"}` |
| `{"component":"Row","align":"center"}` | `{"component":"Row","alignItems":"center"}` |
| `{"component":"Extended.Button"}` | `{"component":"Button"}` |
| `{"styles":{"fontSize":"16fp"}}` | `{"styles":{"fontSize":16}}` |
| `{"columnsTemplate":"repeat(2, 1fr)"}` | `{"columnsTemplate":"1fr 1fr"}` |

部分文档页面仍展示 `Extended.Button` 等旧式自定义组件名，但当前渲染器源码注册的是原生扩展 `Button`。发生冲突时以渲染器注册为准。
