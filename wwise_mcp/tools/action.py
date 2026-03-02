"""
Layer 4 — 操作类工具（6 + 3 个）
"""

import logging
from typing import Any, Union

from ..core.adapter import WwiseAdapter
from ..core.exceptions import WwiseMCPError
from ..rag.doc_index import doc_index

logger = logging.getLogger("wwise_mcp.tools.action")


def _ok(data: Any) -> dict:
    return {"success": True, "data": data, "error": None}

def _err(e: WwiseMCPError) -> dict:
    return e.to_dict()

def _err_raw(code: str, message: str, suggestion: str | None = None) -> dict:
    return {
        "success": False,
        "data": None,
        "error": {"code": code, "message": message, "suggestion": suggestion},
    }


async def create_object(
    name: str,
    obj_type: str,
    parent_path: str,
    on_conflict: str = "rename",
    notes: str = "",
) -> dict:
    """
    在指定父节点下创建 Wwise 对象。

    Args:
        name:        新对象名称
        obj_type:    对象类型，如 'Sound SFX', 'Event', 'Bus', 'BlendContainer' 等
        parent_path: 父对象的完整 WAAPI 路径
        on_conflict: 名称冲突处理策略：'rename'（默认）| 'replace' | 'fail'
        notes:       备注（可选）

    Returns:
        新对象的 {id, name, path}
    """
    try:
        adapter = WwiseAdapter()

        # 安全检查：查询父节点的直接子对象，确认同名对象是否已存在
        existing = await adapter.get_objects(
            from_spec={"path": [parent_path]},
            return_fields=["name", "path"],
            transform=[{"select": ["children"]}],
        )
        existing_names = {obj.get("name") for obj in existing}
        if name in existing_names and on_conflict == "fail":
            return _err_raw(
                "conflict",
                f"父节点 '{parent_path}' 下已存在同名对象 '{name}'",
                "可将 on_conflict 设为 'rename' 自动重命名，或先删除已有对象",
            )

        result = await adapter.create_object(
            name=name,
            obj_type=obj_type,
            parent_path=parent_path,
            on_conflict=on_conflict,
            notes=notes,
        )
        return _ok({
            "id": result.get("id"),
            "name": result.get("name"),
            "path": result.get("path"),
            "type": obj_type,
        })
    except WwiseMCPError as e:
        return _err(e)
    except Exception as e:
        return _err_raw("unexpected_error", str(e))


async def set_property(
    object_path: str,
    property: str | None = None,
    value: Union[float, str, bool, None] = None,
    properties: dict | None = None,
    platform: str | None = None,
) -> dict:
    """
    设置对象的一个或多个属性。

    Args:
        object_path: 目标对象路径
        property:    单个属性名，如 'Volume', 'Pitch', 'LowPassFilter'
        value:       单个属性值
        properties:  批量属性字典，如 {"Volume": -6.0, "Pitch": 200}
        platform:    目标平台（None 表示所有平台）

    注意：property+value 与 properties 二选一，优先使用 properties（批量更高效）
    """
    try:
        adapter = WwiseAdapter()

        # 统一为批量模式
        if properties is None:
            if property is None or value is None:
                return _err_raw(
                    "invalid_param",
                    "必须提供 property+value 或 properties 参数",
                )
            properties = {property: value}

        results = []
        for prop_name, prop_value in properties.items():
            # 防御性校验：属性名必须在已知白名单中
            if not doc_index.is_valid_property(prop_name):
                suggestions = doc_index.get_similar_properties(prop_name)
                results.append({
                    "property": prop_name,
                    "value": prop_value,
                    "success": False,
                    "error": f"未知属性名 '{prop_name}'，请检查拼写",
                    "suggestion": f"相近的合法属性名：{suggestions}" if suggestions else "请调用 get_object_properties 获取合法属性列表",
                })
                continue
            try:
                await adapter.set_property(object_path, prop_name, prop_value, platform)
                results.append({"property": prop_name, "value": prop_value, "success": True})
            except Exception as e:
                results.append({"property": prop_name, "value": prop_value, "success": False, "error": str(e)})

        all_success = all(r["success"] for r in results)
        return _ok({
            "object_path": object_path,
            "results": results,
            "all_success": all_success,
        })
    except WwiseMCPError as e:
        return _err(e)
    except Exception as e:
        return _err_raw("unexpected_error", str(e))


async def create_event(
    event_name: str,
    action_type: str,
    target_path: str,
    parent_path: str = "\\Events\\Default Work Unit",
) -> dict:
    """
    创建 Wwise Event 及其 Action。

    操作顺序（必须严格遵守）：
      1. 创建 Event 对象
      2. 在 Event 下创建 Action
      3. 设置 Action 的 Target 引用

    Args:
        event_name:  Event 名称，建议以动词开头，如 'Play_Explosion'
        action_type: Action 类型：'Play' | 'Stop' | 'Pause' | 'Resume' | 'Break' | 'Mute' | 'UnMute'
        target_path: Action 目标对象路径（Sound/Container 等）
        parent_path: Event 的父节点路径，默认 Default Work Unit

    2024.1 优化：利用 Live Editing 特性，创建后无需生成 SoundBank 即可验证
    """
    try:
        adapter = WwiseAdapter()

        # Step 1: 创建 Event 对象
        event_result = await adapter.create_object(
            name=event_name,
            obj_type="Event",
            parent_path=parent_path,
            on_conflict="rename",
        )
        event_path = event_result.get("path")
        if not event_path:
            return _err_raw("waapi_error", f"创建 Event '{event_name}' 失败：未返回对象路径")

        # Step 2: 在 Event 下创建 Action
        action_name = f"{action_type}_{event_name}"
        action_result = await adapter.create_object(
            name=action_name,
            obj_type="Action",
            parent_path=event_path,
            on_conflict="rename",
        )
        action_path = action_result.get("path")
        if not action_path:
            return _err_raw("waapi_error", f"在 Event 下创建 Action 失败")

        # Step 3: 设置 Action 类型
        action_type_map = {
            "Play": 1, "Stop": 2, "Pause": 3, "Resume": 4,
            "Break": 28, "Mute": 6, "UnMute": 7,
        }
        action_type_id = action_type_map.get(action_type, 1)
        await adapter.set_property(action_path, "ActionType", action_type_id)

        # Step 4: 设置 Action 的 Target 引用
        await adapter.set_reference(action_path, "Target", target_path)

        return _ok({
            "event": {
                "id": event_result.get("id"),
                "name": event_name,
                "path": event_path,
            },
            "action": {
                "id": action_result.get("id"),
                "name": action_name,
                "path": action_path,
                "type": action_type,
                "target": target_path,
            },
            "note": "Wwise 2024.1 Live Editing 已启用，无需重新生成 SoundBank 即可立即验证",
        })
    except WwiseMCPError as e:
        return _err(e)
    except Exception as e:
        return _err_raw("unexpected_error", str(e))


async def assign_bus(object_path: str, bus_path: str) -> dict:
    """
    将对象路由到指定 Bus（设置 OutputBus）。

    Args:
        object_path: 目标 Sound/Container 的路径
        bus_path:    目标 Bus 的完整路径，如 '\\Master-Mixer Hierarchy\\Master Audio Bus\\SFX'
    """
    try:
        adapter = WwiseAdapter()
        # Wwise 要求先启用 OverrideOutput，才能对 Sound/Container 设置 OutputBus
        await adapter.set_property(object_path, "OverrideOutput", True)
        await adapter.set_reference(object_path, "OutputBus", bus_path)
        return _ok({
            "object_path": object_path,
            "output_bus": bus_path,
        })
    except WwiseMCPError as e:
        return _err(e)
    except Exception as e:
        return _err_raw("unexpected_error", str(e))



async def delete_object(object_path: str, force: bool = False) -> dict:
    """
    删除 Wwise 对象。

    Args:
        object_path: 要删除对象的完整路径
        force:       True 时跳过引用检查，直接删除；False（默认）时先检查是否有其他对象引用该目标

    注意：删除前建议先调用 verify_structure 确认无悬空引用
    """
    try:
        adapter = WwiseAdapter()

        if not force:
            # 检查是否有 Action 引用此对象
            # 注意：WAAPI 2024.1 不支持顶层 where 参数，需客户端过滤
            search_result = await adapter.call(
                "ak.wwise.core.object.get",
                {"from": {"ofType": ["Action"]}},
                {"return": ["name", "path", "Target"]},
            )
            all_actions = search_result.get("return", []) if search_result else []
            obj_name = object_path.split("\\")[-1]
            referencing_actions = [
                a for a in all_actions
                if a.get("Target", {}).get("name") == obj_name
            ]
            if referencing_actions:
                return _err_raw(
                    "has_references",
                    f"对象 '{object_path}' 被 {len(referencing_actions)} 个 Action 引用，删除可能导致悬空引用",
                    f"引用该对象的 Action：{[a.get('path') for a in referencing_actions[:5]]}。"
                    f"确认要强制删除请传入 force=True",
                )

        await adapter.delete_object(object_path)
        return _ok({"deleted": object_path})
    except WwiseMCPError as e:
        return _err(e)
    except Exception as e:
        return _err_raw("unexpected_error", str(e))


async def move_object(object_path: str, new_parent_path: str) -> dict:
    """
    将对象移动到新父节点。

    Args:
        object_path:     要移动对象的完整路径
        new_parent_path: 目标父节点路径

    Returns:
        移动后的新路径
    """
    try:
        adapter = WwiseAdapter()
        await adapter.move_object(object_path, new_parent_path)

        # 获取移动后的新路径
        obj_name = object_path.split("\\")[-1]
        new_path = f"{new_parent_path}\\{obj_name}"

        return _ok({
            "original_path": object_path,
            "new_path": new_path,
            "new_parent": new_parent_path,
        })
    except WwiseMCPError as e:
        return _err(e)
    except Exception as e:
        return _err_raw("unexpected_error", str(e))


async def preview_event(event_path: str, action: str = "play") -> dict:
    """
    通过 Wwise Transport API 试听 Event（无需连接游戏实例）。

    Args:
        event_path: Event 的完整 WAAPI 路径，或对象 ID（{XXXXXXXX-...} 格式）
        action:     'play'（默认）| 'stop' | 'pause' | 'resume'

    工作原理：Wwise 内置 Transport 可直接在 Authoring 中预览 Event，
    等同于在 Wwise 里按 F5 试听，无需部署到游戏或生成 SoundBank。
    """
    try:
        adapter = WwiseAdapter()

        valid_actions = {"play", "stop", "pause", "resume"}
        if action not in valid_actions:
            return _err_raw(
                "invalid_param",
                f"不支持的 action：'{action}'",
                f"可用值：{sorted(valid_actions)}",
            )

        if action == "play":
            # 每次 play 创建新 transport 对象
            transport_result = await adapter.call(
                "ak.wwise.core.transport.create",
                {"object": event_path},
            )
            if not transport_result:
                return _err_raw(
                    "waapi_error",
                    "Transport 创建失败，请确认 Event 路径正确且 Wwise 项目已加载",
                    "可先调用 search_objects 或 get_selected_objects 确认路径",
                )
            transport_id = transport_result.get("transport")
            await adapter.call(
                "ak.wwise.core.transport.executeAction",
                {"transport": transport_id, "action": "play"},
            )
            return _ok({
                "event_path": event_path,
                "action": "play",
                "transport_id": transport_id,
                "note": "正在 Wwise Authoring 中预览，调用 preview_event(action='stop') 可停止",
            })
        else:
            # stop/pause/resume 需要有效的 transport_id
            # 兜底：广播 stop-all
            await adapter.call(
                "ak.wwise.core.transport.executeAction",
                {"transport": -1, "action": action},
            )
            return _ok({"action": action, "note": "已对所有 Transport 执行操作"})

    except WwiseMCPError as e:
        return _err(e)
    except Exception as e:
        return _err_raw("unexpected_error", str(e))


# ------------------------------------------------------------------
# RTPC 绑定
# ------------------------------------------------------------------

# 合法的 RTPC 曲线形状
_VALID_CURVE_SHAPES = frozenset({
    "Linear", "Log1", "Log2", "Log3",
    "Exp1", "Exp2", "Exp3",
    "SCurve", "InvertedSCurve", "Constant",
})


async def set_rtpc_binding(
    object_path: str,
    game_parameter_path: str,
    property_name: str = "Volume",
    curve_points: list[dict] | None = None,
    notes: str = "",
) -> dict:
    """
    将 Game Parameter（RTPC）绑定到对象属性，并设置控制曲线。

    通过 ak.wwise.core.object.set 在对象的 @RTPC 列表中创建 RTPC 绑定。

    Args:
        object_path:         目标对象路径（Sound/Container/Bus 等）
        game_parameter_path: Game Parameter 的路径，如 '\\Game Parameters\\Default Work Unit\\Distance'
        property_name:       要控制的属性名，如 'Volume'、'Pitch'、'LowPassFilter'、'OutputBusVolume'
        curve_points:        曲线控制点列表，每个元素为 {"x": float, "y": float, "shape": str}
                             shape 可选值：Linear / Log1~3 / Exp1~3 / SCurve / InvertedSCurve / Constant
                             不提供时使用默认线性曲线 [(0, 0, Linear), (100, 0, Linear)]
        notes:               RTPC 备注（可选）

    Returns:
        绑定结果
    """
    try:
        adapter = WwiseAdapter()

        # 1. 验证目标对象存在
        target_objs = await adapter.get_objects(
            from_spec={"path": [object_path]},
            return_fields=["name", "type", "path", "id"],
        )
        if not target_objs:
            return _err_raw("not_found", f"目标对象不存在：{object_path}",
                            "请先调用 search_objects 搜索正确路径")

        # 2. 验证 Game Parameter 存在并获取其 ID
        gp_objs = await adapter.get_objects(
            from_spec={"path": [game_parameter_path]},
            return_fields=["name", "type", "path", "id"],
        )
        if not gp_objs:
            return _err_raw("not_found", f"Game Parameter 不存在：{game_parameter_path}",
                            "请先调用 get_rtpc_list 查看可用的 Game Parameter，或用 create_object 创建一个")
        gp_id = gp_objs[0].get("id")
        if not gp_id:
            return _err_raw("waapi_error", "无法获取 Game Parameter 的 ID")

        # 3. 构建默认曲线
        if curve_points is None:
            curve_points = [
                {"x": 0, "y": 0, "shape": "Linear"},
                {"x": 100, "y": 0, "shape": "Linear"},
            ]

        # 4. 校验曲线点格式
        for i, pt in enumerate(curve_points):
            if "x" not in pt or "y" not in pt:
                return _err_raw("invalid_param",
                                f"曲线点 [{i}] 缺少 x 或 y 坐标",
                                "每个曲线点必须包含 {x: number, y: number, shape?: string}")
            shape = pt.get("shape", "Linear")
            if shape not in _VALID_CURVE_SHAPES:
                return _err_raw("invalid_param",
                                f"曲线点 [{i}] 的 shape '{shape}' 不合法",
                                f"可选值：{sorted(_VALID_CURVE_SHAPES)}")
            pt["shape"] = shape

        # 5. 构建 object.set payload（WAAPI 官方格式）
        rtpc_entry: dict[str, Any] = {
            "type": "RTPC",
            "name": "",
            "@Curve": {
                "type": "Curve",
                "points": curve_points,
            },
            "@PropertyName": property_name,
            "@ControlInput": gp_id,
        }
        if notes:
            rtpc_entry["notes"] = notes

        result = await adapter.object_set(
            objects=[{
                "object": object_path,
                "@RTPC": [rtpc_entry],
            }],
            list_mode="append",
        )

        return _ok({
            "object_path": object_path,
            "game_parameter": {
                "path": game_parameter_path,
                "id": gp_id,
                "name": gp_objs[0].get("name"),
            },
            "property_name": property_name,
            "curve_points_count": len(curve_points),
            "result": result,
        })
    except WwiseMCPError as e:
        return _err(e)
    except Exception as e:
        return _err_raw("unexpected_error", str(e))


# ------------------------------------------------------------------
# Effect 操作
# ------------------------------------------------------------------

# 常用 Effect classId 映射（Wwise 内置插件）
EFFECT_CLASS_IDS = {
    "RoomVerb": 7733251,
    "Delay": 8454147,
    "Compressor": 613752611,
    "Expander": 7471107,
    "PeakLimiter": 7864323,
    "ParametricEQ": 7995395,
    "MeterFX": 7602179,
    "GainFX": 8126467,
    "MatrixReverb": 8257539,
    "Flanger": 8585219,
    "TremoloFX": 8519683,
    "Harmonizer": 8650755,
    "StereoDelay": 8388611,
    "GuitarDistortion": 8716291,
    "TimeStretch": 8323075,
    "PitchShifter": 8192003,
}


async def add_effect(
    object_path: str,
    effect_name: str,
    effect_plugin: str,
    effect_slot: int = 0,
    effect_params: dict | None = None,
) -> dict:
    """
    为对象或 Bus 添加 Effect 插件。

    通过 ak.wwise.core.object.set 在对象的 @Effects 列表中创建 Effect。

    Args:
        object_path:   目标对象/Bus 路径
        effect_name:   Effect 实例名称，如 'MyReverb'
        effect_plugin: Effect 插件类型名，如 'RoomVerb'、'Delay'、'Compressor'、'ParametricEQ'
                       可用类型见下方列表，也可直接传入 classId 数值
        effect_slot:   Effect 插槽编号（0~3），默认 0
        effect_params: Effect 插件参数（可选），如 {"@PreDelay": 24, "@RoomShape": 99}

    可用 effect_plugin 类型：
        RoomVerb / Delay / Compressor / Expander / PeakLimiter / ParametricEQ
        MeterFX / GainFX / MatrixReverb / Flanger / TremoloFX / Harmonizer
        StereoDelay / GuitarDistortion / TimeStretch / PitchShifter
    """
    try:
        adapter = WwiseAdapter()

        # 1. 验证目标对象存在
        target_objs = await adapter.get_objects(
            from_spec={"path": [object_path]},
            return_fields=["name", "type", "path", "id"],
        )
        if not target_objs:
            return _err_raw("not_found", f"目标对象不存在：{object_path}",
                            "请先调用 search_objects 搜索正确路径")

        # 2. 解析 classId
        if isinstance(effect_plugin, int):
            class_id = effect_plugin
        elif isinstance(effect_plugin, str) and effect_plugin.isdigit():
            class_id = int(effect_plugin)
        elif effect_plugin in EFFECT_CLASS_IDS:
            class_id = EFFECT_CLASS_IDS[effect_plugin]
        else:
            return _err_raw(
                "invalid_param",
                f"未知的 Effect 插件类型：'{effect_plugin}'",
                f"可用类型：{sorted(EFFECT_CLASS_IDS.keys())}，或直接传入 classId 数值",
            )

        # 3. 校验 slot 范围
        if not (0 <= effect_slot <= 3):
            return _err_raw("invalid_param",
                            f"effect_slot 必须在 0~3 之间，收到 {effect_slot}")

        # 4. 构建 Effect 对象
        effect_obj: dict[str, Any] = {
            "type": "Effect",
            "name": effect_name,
            "classId": class_id,
        }
        if effect_params:
            effect_obj.update(effect_params)

        # 5. 构建 object.set payload（WAAPI 官方格式）
        result = await adapter.object_set(
            objects=[{
                "object": object_path,
                "@Effects": [{
                    "type": "EffectSlot",
                    "name": "",
                    "@Effect": effect_obj,
                }],
            }],
            list_mode="append",
        )

        return _ok({
            "object_path": object_path,
            "effect": {
                "name": effect_name,
                "plugin": effect_plugin,
                "classId": class_id,
                "slot": effect_slot,
            },
            "result": result,
        })
    except WwiseMCPError as e:
        return _err(e)
    except Exception as e:
        return _err_raw("unexpected_error", str(e))


async def remove_effect(
    object_path: str,
) -> dict:
    """
    清空对象上的所有 Effect 插槽。

    通过 ak.wwise.core.object.set 的 replaceAll 模式清空 @Effects 列表。
    如需精确移除单个 Effect 并保留其他，请先用 get_effect_chain 查询当前 Effect 链，
    然后用 remove_effect 清空后再用 add_effect 重新添加需要保留的 Effect。

    Args:
        object_path: 目标对象/Bus 路径
    """
    try:
        adapter = WwiseAdapter()

        # 验证目标对象存在
        target_objs = await adapter.get_objects(
            from_spec={"path": [object_path]},
            return_fields=["name", "type", "path"],
        )
        if not target_objs:
            return _err_raw("not_found", f"目标对象不存在：{object_path}",
                            "请先调用 search_objects 搜索正确路径")

        # replaceAll + 空列表 = 清空所有 Effect
        result = await adapter.object_set(
            objects=[{
                "object": object_path,
                "@Effects": [],
            }],
            list_mode="replaceAll",
        )

        return _ok({
            "object_path": object_path,
            "action": "removed_all_effects",
            "result": result,
        })
    except WwiseMCPError as e:
        return _err(e)
    except Exception as e:
        return _err_raw("unexpected_error", str(e))
