# -*- coding: utf-8 -*-
"""批量设置多个对象的属性

典型场景：
  - 统一调整一批 Sound 的音量
  - 批量开启 Streaming
  - 批量设置 Positioning 参数
  - 批量修改 Notes 标记
"""

SKILL_INFO = {
    "name": "batch_set_property",
    "description": (
        "批量设置多个对象的属性。支持两种模式：\n"
        "1. 对指定路径列表统一设置相同属性（targets + properties）\n"
        "2. 对每个对象设置不同属性（items 数组，每项含 path 和 properties）\n"
        "全部操作包裹在 Undo Group 中，可一键撤销。"
    ),
    "parameters": {
        "targets": {
            "type": "array",
            "description": "对象路径列表（模式1：统一设置同样的属性）",
            "required": False,
        },
        "properties": {
            "type": "object",
            "description": "属性名→值的字典（模式1：配合 targets 使用）",
            "required": False,
        },
        "items": {
            "type": "array",
            "description": (
                "模式2：每项含 path(str) 和 properties(dict)，"
                "可为不同对象设置不同属性"
            ),
            "required": False,
        },
        "type_filter": {
            "type": "string",
            "description": (
                "按类型过滤快捷方式：不传 targets，而是指定类型名 "
                "（如 'Sound'），自动对项目中所有该类型对象设置属性"
            ),
            "required": False,
        },
        "name_filter": {
            "type": "string",
            "description": "配合 type_filter 使用，按名称关键词进一步过滤",
            "required": False,
        },
    },
}


def run(targets=None, properties=None, items=None,
        type_filter=None, name_filter=None):
    from ._waapi_helpers import (
        waapi_call, set_property, set_reference,
        get_objects, is_valid_property, ok, err,
    )

    # ── 参数校验 ──
    if items:
        # 模式2：每项独立
        work_items = []
        for item in items:
            path = item.get("path")
            props = item.get("properties", {})
            if not path or not props:
                continue
            work_items.append((path, props))
    elif targets and properties:
        # 模式1：统一设置
        work_items = [(t, properties) for t in targets]
    elif type_filter and properties:
        # 快捷模式：按类型过滤
        try:
            found = get_objects(
                from_spec={"ofType": [type_filter]},
                return_fields=["name", "path"],
            )
            if name_filter:
                kw = name_filter.lower()
                found = [o for o in found if kw in o.get("name", "").lower()]
            work_items = [(o["path"], properties) for o in found]
        except Exception as e:
            return err("filter_failed", f"按类型 '{type_filter}' 查询失败: {e}")
    else:
        return err(
            "invalid_param",
            "必须提供以下之一：(1) targets + properties，(2) items 数组，(3) type_filter + properties",
        )

    if not work_items:
        return err("no_targets", "没有匹配的目标对象")

    # 引用型属性（需要用 setReference 而非 setProperty）
    REFERENCE_PROPS = {"OutputBus", "Target", "AttenuationShareSet",
                       "Positioning.3D.AttenuationID"}

    # ── Undo Group ──
    try:
        waapi_call("ak.wwise.core.undo.beginGroup")
        undo_opened = True
    except Exception:
        undo_opened = False

    try:
        results = {"success": 0, "failed": 0, "skipped": 0, "details": []}

        for obj_path, props in work_items:
            obj_result = {"path": obj_path, "properties": []}
            for prop_name, prop_value in props.items():
                try:
                    if prop_name in REFERENCE_PROPS:
                        set_reference(obj_path, prop_name, prop_value)
                    else:
                        set_property(obj_path, prop_name, prop_value)
                    obj_result["properties"].append({
                        "name": prop_name, "value": prop_value, "success": True
                    })
                    results["success"] += 1
                except Exception as e:
                    obj_result["properties"].append({
                        "name": prop_name, "value": prop_value,
                        "success": False, "error": str(e)
                    })
                    results["failed"] += 1
            results["details"].append(obj_result)

        # ── Undo Group 结束 ──
        if undo_opened:
            try:
                count = results["success"] + results["failed"]
                waapi_call("ak.wwise.core.undo.endGroup",
                           {"displayName": f"Wwise Agent: Batch Set Property ({count} ops)"})
            except Exception:
                pass

        # 压缩详情输出（超过 20 个只显示失败项）
        if len(results["details"]) > 20:
            failed_details = [
                d for d in results["details"]
                if any(not p["success"] for p in d["properties"])
            ]
            results["details"] = failed_details[:20]
            results["details_note"] = f"仅显示失败项（共 {len(work_items)} 个对象操作）"

        return ok({
            "total_objects": len(work_items),
            "total_success": results["success"],
            "total_failed": results["failed"],
            "details": results["details"],
            "details_note": results.get("details_note"),
            "undo": "可通过 Wwise Ctrl+Z 一键撤销全部修改" if undo_opened else None,
        })

    except Exception as e:
        if undo_opened:
            try:
                waapi_call("ak.wwise.core.undo.cancelGroup")
            except Exception:
                pass
        return err("batch_set_property_failed", str(e))
