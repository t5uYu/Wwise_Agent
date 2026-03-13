# -*- coding: utf-8 -*-
"""批量创建 Wwise 对象（支持 Undo Group 原子操作）

典型场景：
  - 一次创建多个 Sound、Container、Event
  - 嵌套创建（父子结构），利用 object.set 的 children 字段
  - 批量生成命名规则化的对象序列
"""

SKILL_INFO = {
    "name": "batch_create",
    "description": (
        "批量创建多个 Wwise 对象。支持两种模式：\n"
        "1. flat 模式：在同一父节点下创建多个同级对象（传 objects 数组）\n"
        "2. tree 模式：一次性创建嵌套层级结构（传 tree，含 children 递归）\n"
        "全部操作包裹在 Undo Group 中，可一键撤销。"
    ),
    "parameters": {
        "parent_path": {
            "type": "string",
            "description": "父节点路径（flat 模式必填，tree 模式可选——作为 tree 根节点的父路径）",
            "required": True,
        },
        "objects": {
            "type": "array",
            "description": (
                "flat 模式：对象数组，每项含 name(str), type(str), "
                "notes(str, 可选), properties(dict, 可选)"
            ),
            "required": False,
        },
        "tree": {
            "type": "object",
            "description": (
                "tree 模式：嵌套结构，含 name, type, children(递归数组), "
                "notes(可选), properties(可选)"
            ),
            "required": False,
        },
        "on_conflict": {
            "type": "string",
            "description": "同名冲突策略：rename(默认) / fail / merge / replace",
            "required": False,
        },
    },
}


def _build_object_set_item(parent_path, obj, on_conflict):
    """将单个对象描述转换为 object.set 的 item 格式"""
    item = {
        "object": parent_path,
        "name": obj["name"],
        "type": obj["type"],
        "onNameConflict": on_conflict,
    }
    if obj.get("notes"):
        item["notes"] = obj["notes"]
    # children 递归
    if obj.get("children"):
        item["children"] = []
        for child in obj["children"]:
            child_item = {
                "name": child["name"],
                "type": child["type"],
                "onNameConflict": on_conflict,
            }
            if child.get("notes"):
                child_item["notes"] = child["notes"]
            if child.get("children"):
                child_item["children"] = _build_children_recursive(child["children"], on_conflict)
            item["children"].append(child_item)
    return item


def _build_children_recursive(children, on_conflict):
    """递归构建 children 列表"""
    result = []
    for child in children:
        child_item = {
            "name": child["name"],
            "type": child["type"],
            "onNameConflict": on_conflict,
        }
        if child.get("notes"):
            child_item["notes"] = child["notes"]
        if child.get("children"):
            child_item["children"] = _build_children_recursive(child["children"], on_conflict)
        result.append(child_item)
    return result


def _collect_properties(objects):
    """收集需要设置的属性（object.set 不支持直接设属性，需后续逐个设）"""
    props_to_set = []
    for obj in objects:
        if obj.get("properties"):
            props_to_set.append((obj["name"], obj["properties"]))
        for child in obj.get("children", []):
            if child.get("properties"):
                props_to_set.append((child["name"], child["properties"]))
    return props_to_set


def run(parent_path, objects=None, tree=None, on_conflict="rename"):
    from ._waapi_helpers import waapi_call, object_set, get_objects, set_property, ok, err

    if not objects and not tree:
        return err("invalid_param", "必须提供 objects（flat 模式）或 tree（tree 模式）之一")

    try:
        # ── Undo Group 开始 ──
        waapi_call("ak.wwise.core.undo.beginGroup")
        undo_opened = True
    except Exception:
        undo_opened = False

    try:
        created = []
        props_to_set = []

        if tree:
            # ── tree 模式：单次 object.set 创建嵌套结构 ──
            items = [_build_object_set_item(parent_path, tree, on_conflict)]
            if tree.get("properties"):
                props_to_set.append((tree["name"], tree["properties"]))
            props_to_set.extend(_collect_properties([tree]))
            object_set(items, on_name_conflict=on_conflict)
            # 查询创建结果
            root_objs = get_objects(
                from_spec={"path": [parent_path]},
                return_fields=["name", "path", "type", "id"],
                transform=[{"select": ["descendants"]}],
            )
            created = root_objs

        else:
            # ── flat 模式：在同一父节点下批量创建 ──
            items = []
            for obj in objects:
                item = {
                    "object": parent_path,
                    "name": obj["name"],
                    "type": obj["type"],
                    "onNameConflict": on_conflict,
                }
                if obj.get("notes"):
                    item["notes"] = obj["notes"]
                if obj.get("children"):
                    item["children"] = _build_children_recursive(obj.get("children", []), on_conflict)
                items.append(item)
                if obj.get("properties"):
                    props_to_set.append((obj["name"], obj["properties"]))

            object_set(items, on_name_conflict=on_conflict)

            # 查询创建结果
            child_objs = get_objects(
                from_spec={"path": [parent_path]},
                return_fields=["name", "path", "type", "id"],
                transform=[{"select": ["children"]}],
            )
            request_names = {o["name"] for o in objects}
            created = [c for c in child_objs if c.get("name") in request_names]

        # ── 后设属性 ──
        prop_results = []
        for obj_name, props in props_to_set:
            matching = [c for c in created if c.get("name") == obj_name]
            if matching:
                obj_path = matching[0].get("path")
                for prop_name, prop_value in props.items():
                    try:
                        set_property(obj_path, prop_name, prop_value)
                        prop_results.append({"object": obj_name, "property": prop_name, "success": True})
                    except Exception as e:
                        prop_results.append({"object": obj_name, "property": prop_name, "success": False, "error": str(e)})

        # ── Undo Group 结束 ──
        if undo_opened:
            try:
                waapi_call("ak.wwise.core.undo.endGroup", {"displayName": "Wwise Agent: Batch Create"})
            except Exception:
                pass

        return ok({
            "created_count": len(created),
            "created": [{"name": c.get("name"), "path": c.get("path"), "type": c.get("type")} for c in created[:50]],
            "property_results": prop_results if prop_results else None,
            "undo": "可通过 Wwise Ctrl+Z 一键撤销全部创建" if undo_opened else None,
        })

    except Exception as e:
        # 异常时也要关闭 Undo Group
        if undo_opened:
            try:
                waapi_call("ak.wwise.core.undo.cancelGroup")
            except Exception:
                pass
        return err("batch_create_failed", str(e),
                   "请检查父路径是否存在、对象类型是否合法")
