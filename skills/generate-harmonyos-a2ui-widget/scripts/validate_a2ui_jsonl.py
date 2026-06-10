#!/usr/bin/env python3
"""校验鸿蒙 A2UI 桌面卡片 JSONL 的结构约束。"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


MESSAGE_KEYS = {
    "createSurface",
    "updateComponents",
    "updateDataModel",
    "deleteSurface",
}
EXTENDED_COMPONENTS = {
    "Button",
    "Text",
    "TextInput",
    "Row",
    "Column",
    "List",
    "Stack",
    "Grid",
    "Image",
    "Divider",
    "Toggle",
    "Progress",
    "Radio",
    "Checkbox",
    "CheckboxGroup",
    "If",
    "Extended.Select",
    "Extended.Navigation",
    "Extended.Tabs",
    "Extended.TabContent",
    "Extended.Web",
}
PATH_RE = re.compile(r"^/(?:[^~/]|~[01])*(?:/(?:[^~/]|~[01])*)*$")


def walk(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def root_field(path: str) -> str | None:
    if not path.startswith("/") or path == "/":
        return None
    token = path.split("/", 2)[1]
    return token.replace("~1", "/").replace("~0", "~")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    if len(sys.argv) != 2:
        print("用法：validate_a2ui_jsonl.py <文件.jsonl>")
        return 2

    path = Path(sys.argv[1])
    errors: list[str] = []
    warnings: list[str] = []
    messages: list[tuple[int, dict[str, Any], str]] = []

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        print(f"错误：无法读取 {path}：{exc}")
        return 2

    for number, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"第 {number} 行：JSON 无效：{exc.msg}")
            continue
        if not isinstance(obj, dict):
            errors.append(f"第 {number} 行：消息信封必须是对象")
            continue
        if obj.get("version") != "v0.9":
            errors.append(f"第 {number} 行：version 必须是 v0.9")
        bodies = [key for key in MESSAGE_KEYS if key in obj]
        if len(bodies) != 1:
            errors.append(
                f"第 {number} 行：消息信封必须且只能包含一个消息体"
            )
            continue
        extra = set(obj) - {"version", bodies[0]}
        if extra:
            warnings.append(
                f"第 {number} 行：消息信封包含未预期字段：{sorted(extra)}"
            )
        body = obj[bodies[0]]
        if not isinstance(body, dict):
            errors.append(f"第 {number} 行：{bodies[0]} 消息体必须是对象")
            continue
        messages.append((number, body, bodies[0]))

    if not messages:
        errors.append("未找到有效的 A2UI 消息")

    surface_ids: set[str] = set()
    create_positions: list[int] = []
    catalog_id: str | None = None
    components: dict[str, dict[str, Any]] = {}
    component_lines: dict[str, int] = {}
    data_roots: set[str] = set()
    absolute_bindings: list[tuple[int, str]] = []

    for position, (number, body, kind) in enumerate(messages):
        surface_id = body.get("surfaceId")
        if not isinstance(surface_id, str) or not surface_id:
            errors.append(f"第 {number} 行：{kind}.surfaceId 为必填字段")
        else:
            surface_ids.add(surface_id)

        if kind == "createSurface":
            create_positions.append(position)
            catalog_id = body.get("catalogId")
            if catalog_id != "ohos.a2ui.extended.catalog":
                warnings.append(
                    f"第 {number} 行：本校验器主要面向 "
                    "ohos.a2ui.extended.catalog"
                )

        if kind == "updateComponents":
            items = body.get("components")
            if not isinstance(items, list):
                errors.append(f"第 {number} 行：components 必须是数组")
                continue
            for component in items:
                if not isinstance(component, dict):
                    errors.append(f"第 {number} 行：组件必须是对象")
                    continue
                component_id = component.get("id")
                component_type = component.get("component")
                if not isinstance(component_id, str) or not component_id:
                    errors.append(f"第 {number} 行：组件 id 为必填字段")
                    continue
                if component_id in components:
                    warnings.append(
                        f"第 {number} 行：组件 {component_id!r} 被再次更新"
                    )
                components[component_id] = component
                component_lines[component_id] = number
                if not isinstance(component_type, str):
                    errors.append(
                        f"第 {number} 行：组件 {component_id!r} 缺少 component 类型"
                    )
                elif catalog_id == "ohos.a2ui.extended.catalog":
                    if component_type not in EXTENDED_COMPONENTS:
                        errors.append(
                            f"第 {number} 行：不支持的扩展组件 "
                            f"{component_type!r}"
                        )
                    if component_type.startswith("Extended.") and component_type in {
                        "Extended.Text",
                        "Extended.Button",
                        "Extended.Column",
                        "Extended.Row",
                        "Extended.Image",
                    }:
                        errors.append(
                            f"第 {number} 行：{component_type} 应使用不带 "
                            "Extended. 前缀的原生组件名"
                        )

                if component_type == "Text" and "text" in component:
                    errors.append(
                        f"第 {number} 行：扩展 Text {component_id!r} 应使用 "
                        "'content'，不能使用 'text'"
                    )
                if component_type == "Image" and "url" in component:
                    errors.append(
                        f"第 {number} 行：扩展 Image {component_id!r} 应使用 "
                        "'src'，不能使用 'url'"
                    )
                if component_type == "Button" and "child" in component:
                    errors.append(
                        f"第 {number} 行：扩展 Button {component_id!r} 应使用 "
                        "'label'，不能使用 'child'"
                    )
                if component_type in {"Row", "Column"}:
                    if "justify" in component:
                        errors.append(
                            f"第 {number} 行：扩展 {component_type} "
                            f"{component_id!r} 应使用 'justifyContent'"
                        )
                    if "align" in component:
                        errors.append(
                            f"第 {number} 行：扩展 {component_type} "
                            f"{component_id!r} 应使用 'alignItems'"
                        )
                if component_type == "Grid":
                    columns = component.get("columnsTemplate")
                    if isinstance(columns, str) and "repeat(" in columns:
                        errors.append(
                            f"第 {number} 行：Grid columnsTemplate 不支持 repeat()"
                        )
                if component_type == "Divider":
                    misplaced = [
                        key
                        for key in ("vertical", "strokeWidth", "color")
                        if key in component
                    ]
                    if misplaced:
                        errors.append(
                            f"第 {number} 行：Divider {component_id!r} 必须将 "
                            f"{misplaced} 放入 styles"
                        )
                if component_type == "If" and "childrenElse" not in component:
                    warnings.append(
                        f"第 {number} 行：If {component_id!r} 缺少 childrenElse"
                    )

                styles = component.get("styles")
                if isinstance(styles, dict):
                    for key in ("fontSize", "minFontSize", "maxFontSize"):
                        value = styles.get(key)
                        if isinstance(value, str) and not value.strip().startswith("{{"):
                            errors.append(
                                f"第 {number} 行：组件 {component_id!r} 的 "
                                f"styles.{key} 必须是数值"
                            )

                for node in walk(component):
                    bound_path = node.get("path")
                    if isinstance(bound_path, str) and bound_path.startswith("/"):
                        if not PATH_RE.match(bound_path):
                            errors.append(
                                f"第 {number} 行：JSON Pointer 无效：{bound_path!r}"
                            )
                        absolute_bindings.append((number, bound_path))

        if kind == "updateDataModel":
            update_path = body.get("path", "/")
            if update_path == "/" and isinstance(body.get("value"), dict):
                data_roots.update(body["value"].keys())
            elif isinstance(update_path, str):
                field = root_field(update_path)
                if field:
                    data_roots.add(field)

    if create_positions and create_positions[0] != 0:
        errors.append("createSurface 必须是第一条消息")
    if len(create_positions) != 1:
        errors.append("消息流必须且只能包含一条 createSurface")
    if len(surface_ids) > 1:
        errors.append(f"消息使用了多个 surfaceId：{sorted(surface_ids)}")
    if "root" not in components:
        errors.append("组件图必须定义 id 为 'root' 的根组件")

    known_ids = set(components)
    for component_id, component in components.items():
        number = component_lines[component_id]
        children = component.get("children")
        refs: list[str] = []
        if isinstance(children, list):
            refs.extend(value for value in children if isinstance(value, str))
        elif isinstance(children, dict):
            template_id = children.get("componentId")
            if isinstance(template_id, str):
                refs.append(template_id)
            template_path = children.get("path")
            if not isinstance(template_path, str):
                errors.append(
                    f"第 {number} 行：组件 {component_id!r} 的模板 children 缺少 path"
                )
        component_type = component.get("component")
        if component_type == "Card":
            value = component.get("child")
            if isinstance(value, str):
                refs.append(value)
        if component_type == "Modal":
            for field in ("trigger", "content"):
                value = component.get(field)
                if isinstance(value, str):
                    refs.append(value)
        for field in ("childrenIf", "childrenElse"):
            value = component.get(field)
            if isinstance(value, list):
                refs.extend(item for item in value if isinstance(item, str))
        for ref in refs:
            if ref not in known_ids:
                errors.append(
                    f"第 {number} 行：组件 {component_id!r} 引用了 "
                    f"未定义的 id {ref!r}"
                )

    for number, binding in absolute_bindings:
        field = root_field(binding)
        if field and data_roots and field not in data_roots:
            warnings.append(
                f"第 {number} 行：绑定 {binding!r} 对应的根字段 "
                f"{field!r} 未初始化"
            )

    for item in errors:
        print(f"错误：{item}")
    for item in warnings:
        print(f"警告：{item}")
    print(
        f"已校验 {len(messages)} 条消息、{len(components)} 个组件："
        f"{len(errors)} 个错误，{len(warnings)} 个警告"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
