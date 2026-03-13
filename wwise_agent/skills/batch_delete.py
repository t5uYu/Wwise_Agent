# -*- coding: utf-8 -*-
"""批量删除 Wwise 对象

典型场景：
  - 清理一批测试用的临时对象
  - 删除搜索结果中匹配的所有对象
  - 按类型 + 名称模式批量清理冗余资源
"""

SKILL_INFO = {
    "name": "batch_delete",
    "description": (
        "批量删除多个 Wwise 对象。支持两种目标指定方式：\n"
        "1. 直接传入路径列表 (paths)\n"
        "2. 按类型 + 名称关键词过滤 (type_filter + name_filter)\n"
        "默认会检查引用关系，被 Event Action 引用的对象跳过（除非 force=true）。\n"
        "全部操作包裹在 Undo Group 中，可一键撤销。"
    ),
    "parameters": {
        "paths": {
            "type": "array",
            "description": "要删除的对象路径列表",
            "required": False,
        },
        "type_filter": {
            "type": "string",
            "description": "按类型过滤（如 'Sound', 'Event'），配合 name_filter 使用",
            "required": False,
        },
        "name_filter": {
            "type": "string",
            "description": "名称关键词过滤（大小写不敏感）",
            "required": False,
        },
        "force": {
            "type": "boolean",
            "description": "是否跳过引用检查强制删除，默认 false",
            "required": False,
        },
        "dry_run": {
            "type": "boolean",
            "description": "试运行模式：只返回将被删除的对象列表，不实际删除",
            "required": False,
        },
    },
}


def run(paths=None, type_filter=None, name_filter=None, force=False, dry_run=False):
    from ._waapi_helpers import waapi_call, delete_object, get_objects, ok, err

    # ── 确定目标列表 ──
    if paths:
        targets = [{"path": p} for p in paths]
    elif type_filter:
        try:
            found = get_objects(
                from_spec={"ofType": [type_filter]},
                return_fields=["name", "path", "type", "id"],
            )
            if name_filter:
                kw = name_filter.lower()
                found = [o for o in found if kw in o.get("name", "").lower()]
            targets = found
        except Exception as e:
            return err("filter_failed", f"查询类型 '{type_filter}' 失败: {e}")
    else:
        return err("invalid_param", "必须提供 paths 列表或 type_filter 参数")

    if not targets:
        return ok({"deleted_count": 0, "message": "没有匹配的目标对象"})

    # ── 引用检查 ──
    referenced = {}
    if not force:
        try:
            actions = get_objects(
                from_spec={"ofType": ["Action"]},
                return_fields=["name", "path", "Target"],
            )
            target_names = set()
            for a in actions:
                t = a.get("Target")
                if isinstance(t, dict) and t.get("name"):
                    target_names.add(t["name"])
            for t in targets:
                obj_name = t.get("name") or t.get("path", "").split("\\")[-1]
                if obj_name in target_names:
                    referenced[t.get("path")] = obj_name
        except Exception:
            pass  # 引用检查失败不阻断，继续执行

    # ── dry_run 模式 ──
    if dry_run:
        will_delete = []
        will_skip = []
        for t in targets:
            p = t.get("path", "")
            info = {"path": p, "name": t.get("name", p.split("\\")[-1])}
            if p in referenced:
                info["skip_reason"] = f"被 Action 引用"
                will_skip.append(info)
            else:
                will_delete.append(info)
        return ok({
            "dry_run": True,
            "will_delete_count": len(will_delete),
            "will_skip_count": len(will_skip),
            "will_delete": will_delete[:50],
            "will_skip": will_skip[:20],
        })

    # ── 实际删除 ──
    try:
        waapi_call("ak.wwise.core.undo.beginGroup")
        undo_opened = True
    except Exception:
        undo_opened = False

    try:
        deleted = []
        skipped = []
        failed = []

        for t in targets:
            path = t.get("path", "")
            name = t.get("name", path.split("\\")[-1])

            if path in referenced and not force:
                skipped.append({"path": path, "name": name, "reason": "被 Action 引用"})
                continue

            try:
                delete_object(path)
                deleted.append({"path": path, "name": name})
            except Exception as e:
                failed.append({"path": path, "name": name, "error": str(e)})

        if undo_opened:
            try:
                waapi_call("ak.wwise.core.undo.endGroup",
                           {"displayName": f"Wwise Agent: Batch Delete ({len(deleted)} objects)"})
            except Exception:
                pass

        return ok({
            "deleted_count": len(deleted),
            "skipped_count": len(skipped),
            "failed_count": len(failed),
            "deleted": deleted[:50],
            "skipped": skipped[:20] if skipped else None,
            "failed": failed[:20] if failed else None,
            "undo": "可通过 Wwise Ctrl+Z 一键撤销全部删除" if undo_opened else None,
        })

    except Exception as e:
        if undo_opened:
            try:
                waapi_call("ak.wwise.core.undo.cancelGroup")
            except Exception:
                pass
        return err("batch_delete_failed", str(e))
