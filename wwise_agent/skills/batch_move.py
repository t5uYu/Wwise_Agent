# -*- coding: utf-8 -*-
"""批量移动 Wwise 对象到新父节点

典型场景：
  - 将一批 Sound 从一个 ActorMixer 移到另一个
  - 重组项目结构，将某类型下的所有对象移入新 Folder
  - 按搜索结果批量归档
"""

SKILL_INFO = {
    "name": "batch_move",
    "description": (
        "批量移动多个 Wwise 对象到新父节点。支持两种模式：\n"
        "1. 统一目标：所有 source_paths 移到同一个 target_parent\n"
        "2. 独立映射：items 数组，每项含 source_path 和 target_parent\n"
        "全部操作包裹在 Undo Group 中，可一键撤销。"
    ),
    "parameters": {
        "source_paths": {
            "type": "array",
            "description": "要移动的对象路径列表（模式1）",
            "required": False,
        },
        "target_parent": {
            "type": "string",
            "description": "统一的目标父节点路径（模式1）",
            "required": False,
        },
        "items": {
            "type": "array",
            "description": (
                "模式2：每项含 source_path(str) 和 target_parent(str)"
            ),
            "required": False,
        },
        "on_conflict": {
            "type": "string",
            "description": "同名冲突策略：rename(默认) / fail / replace",
            "required": False,
        },
    },
}


def run(source_paths=None, target_parent=None, items=None, on_conflict="rename"):
    from ._waapi_helpers import waapi_call, move_object, ok, err

    # ── 构建工作列表 ──
    if items:
        work_items = [
            (item["source_path"], item["target_parent"])
            for item in items
            if item.get("source_path") and item.get("target_parent")
        ]
    elif source_paths and target_parent:
        work_items = [(sp, target_parent) for sp in source_paths]
    else:
        return err(
            "invalid_param",
            "必须提供 (source_paths + target_parent) 或 items 数组",
        )

    if not work_items:
        return ok({"moved_count": 0, "message": "没有需要移动的对象"})

    # ── Undo Group ──
    try:
        waapi_call("ak.wwise.core.undo.beginGroup")
        undo_opened = True
    except Exception:
        undo_opened = False

    try:
        moved = []
        failed = []

        for source_path, dest_parent in work_items:
            try:
                move_object(source_path, dest_parent)
                obj_name = source_path.split("\\")[-1]
                moved.append({
                    "original_path": source_path,
                    "new_parent": dest_parent,
                    "new_path": f"{dest_parent}\\{obj_name}",
                })
            except Exception as e:
                failed.append({
                    "source_path": source_path,
                    "target_parent": dest_parent,
                    "error": str(e),
                })

        if undo_opened:
            try:
                waapi_call("ak.wwise.core.undo.endGroup",
                           {"displayName": f"Wwise Agent: Batch Move ({len(moved)} objects)"})
            except Exception:
                pass

        return ok({
            "moved_count": len(moved),
            "failed_count": len(failed),
            "moved": moved[:50],
            "failed": failed[:20] if failed else None,
            "undo": "可通过 Wwise Ctrl+Z 一键撤销全部移动" if undo_opened else None,
        })

    except Exception as e:
        if undo_opened:
            try:
                waapi_call("ak.wwise.core.undo.cancelGroup")
            except Exception:
                pass
        return err("batch_move_failed", str(e))
