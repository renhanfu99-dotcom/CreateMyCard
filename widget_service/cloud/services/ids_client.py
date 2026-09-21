# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2026-2026. All rights reserved.
import base64
import hashlib
import hmac
import json
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import requests

from app.logger import json_for_log, logger
from config.config import get_settings
from models.generation import DeviceContext
from models.service import (
    IDSHttpRequest,
    IDSInstalledAppsQueryBody,
    IDSNamespaceQuery,
    IDSQueryKeys,
    IDSQueryRequestData,
    IDSRequestHeaders,
)
from services.json_loader import load_json
from utils.base_utils import sts_config

_MODULE = "[IDS Client]"

# IDS 业务错误码。范围错误码（SDS/DCS/DMQ）在精确码未维护时使用范围描述。
IDS_ERROR_DESCRIPTIONS: dict[int, str] = {
    2: "参数非法",
    6: "华为账号认证失败",
    7: "访问被流控",
    8: "访问被流控",
    13: "鉴权失败",
    10000: "内部通用错误",
    10001: "服务执行异常",
    10003: "服务执行超时",
    10018: "MySQL处理失败",
    300000: "CSS检索结果为空",
    413302: "SDS表参数非法",
    413307: "SDS表不存在",
    413326: "SDS黑名单拦截",
    64001: "DCS健康检查失败",
    64002: "DCS请求失败",
    80002: "DMQ消息发送失败",
    80003: "DMQ订阅消息失败",
}


def describe_ids_error(ret_code: Any) -> str:
    """返回 IDS 错误码的可读描述，未知码保留其所属处理模块。"""
    try:
        code = int(ret_code)
    except (TypeError, ValueError):
        return "未知 IDS 错误"

    exact_description = IDS_ERROR_DESCRIPTIONS.get(code)
    if exact_description:
        return exact_description
    if 400000 <= code < 500000:
        return "SDS处理失败"
    if 60000 <= code < 70000:
        return "DCS处理失败"
    if 80000 <= code < 90000:
        return "DMQ处理失败"
    return "未知 IDS 错误"


def _is_success_ret_code(ret_code: Any) -> bool:
    """兼容 IDS 将 retCode 编码为整数或数字字符串的响应。"""
    try:
        return int(ret_code) == 0
    except (TypeError, ValueError):
        return False


@dataclass(frozen=True)
class IDSDeviceCapabilityState:
    """微服务内部使用的 IDS 已安装应用快照。"""

    installed_apps: set[str] = field(default_factory=set)


class IDSClient:
    """IDS 查询客户端。

    mock 开启时只读取本地 IDS 响应文件；mock 关闭时只请求真实 IDS。
    `DeviceCapabilityResolver` 始终消费稳定的 `IDSDeviceCapabilityState`。
    """

    def __init__(self, mock_response_path: Path | None = None) -> None:
        """初始化 IDS 客户端。

        入参：
        - mock_response_path：可选 mock IDS 响应路径；不传时读取全局配置。
        出参：无。
        """
        self.settings = get_settings()
        # 测试和本地调试可显式传入文件路径；是否读取该文件仅由 enable_ids_mock 决定。
        self.mock_response_path = (
            mock_response_path or self.settings.resolved_mock_ids_response_path
        )

    def build_installed_apps_query(
        self,
        device: DeviceContext,
        request_id: str,
    ) -> IDSHttpRequest:
        """构造 IDS 已安装应用查询请求。

        入参：
        - device：工具层注入的设备信息，优先使用 odid，缺失时使用固定默认 odid。
        - request_id：本次 IDS 查询请求 ID。
        出参：结构化 IDS HTTP 请求定义；后续真实 HTTP 调用可直接使用。
        """
        # 请求结构来自一次性 Postman 导出样例，代码内固化成实体对象后不再依赖 collection 文件。
        odid = device.odid or "790d8366-cd45-c4d5-6784-06727a549e61"
        query_data = [IDSQueryRequestData(keys=IDSQueryKeys(odid=odid))]
        body = IDSInstalledAppsQueryBody(
            requestId=request_id,
            callingUid=self.settings.ids_calling_uid,
            nameSpaces=[
                IDSNamespaceQuery(
                    dataType="t_ids_kv_ohos_installed_apps",
                    queryRequestData=query_data,
                ),
            ],
        )
        ids_sign = self.build_ids_sign(
            timestamp_ms=int(time.time() * 1000),
        )
        logger.info(
            f"{_MODULE} ids_device_capability_query_built request_id={request_id} "
            f"odid_source={'content' if device.odid else 'default'} "
            f"body={json_for_log(body.model_dump(mode='json'))} "
            f"ids_sign_preview={ids_sign[:8]}"
        )
        return IDSHttpRequest(
            method="POST",
            url=self.settings.ids_query_url,
            headers=IDSRequestHeaders(
                **{
                    "Content-Type": "application/json",
                    "devFakeId": self.settings.ids_dev_fake_id,
                    "idsSign": ids_sign,
                }
            ),
            body=body,
        )

    def build_ids_sign(
        self,
        timestamp_ms: int | None = None,
    ) -> str:
        """生成 IDS 请求签名。

        入参：
        - timestamp_ms：毫秒时间戳；不传时使用当前时间。
        出参：`accessKey;timestamp;sign` 格式的 IDS 签名字符串。
        """
        ts = timestamp_ms or int(time.time() * 1000)
        access_key = self.settings.ids_access_key
        secret_key_bytes = self._decode_ids_secret_key(sts_config.get_sts_config("ids.secret.key"))
        sign_source = f"{access_key}{ts}".encode()
        digest = hmac.new(secret_key_bytes, sign_source, hashlib.sha256).digest()
        sign = base64.b64encode(digest).decode("utf-8")
        return f"{access_key};{ts};{sign}"

    def _decode_ids_secret_key(self, secret_key: str | bytes) -> bytes:
        """解析 IDS secretKey。

        入参：
        - secret_key：配置中的 secretKey，按 Postman 脚本约定优先视为 Base64。
        出参：HMAC 使用的 key bytes。
        """
        if isinstance(secret_key, bytes):
            return secret_key
        try:
            padding = "=" * (-len(secret_key) % 4)
            return base64.b64decode(secret_key + padding, validate=True)
        except ValueError:
            # 本地 dummy 配置可能不是合法 Base64；兜底使用原始字符串，避免本地启动直接失败。
            return secret_key.encode("utf-8")

    def get_device_capability_state(
        self,
        device: DeviceContext,
        request_id: str,
    ) -> IDSDeviceCapabilityState:
        """获取设备已安装应用状态。

        入参：
        - device：工具层注入的设备信息，用于构造 IDS 查询条件。
        - request_id：本次 IDS 查询请求 ID。
        出参：标准化后的 IDSDeviceCapabilityState，供依赖包名匹配使用。
        """
        if self.settings.enable_ids_mock:
            return self._load_mock_state(request_id)

        # mock 关闭时忽略本地文件，只构造并访问真实 IDS 请求。
        ids_query = self.build_installed_apps_query(device, request_id)
        logger.info(
            f"{_MODULE} ids_device_capability_query_prepared request_id={request_id} "
            f"method={ids_query.method} url={ids_query.url} "
            f"headers={json_for_log(self._safe_headers_for_log(ids_query))} "
            f"body={json_for_log(ids_query.body.model_dump(mode='json'))}"
        )
        payload = self._query_remote_ids(ids_query, request_id)
        state = self._parse_ids_payload(payload)
        logger.info(
            f"{_MODULE} ids_device_capability_state_loaded request_id={request_id} "
            f"source=remote installed_app_count={len(state.installed_apps)}"
        )
        return state

    def _load_mock_state(self, request_id: str) -> IDSDeviceCapabilityState:
        """只读取并解析本地 IDS mock；任何失败都返回空状态且不访问远端。"""
        try:
            logger.info(
                f"{_MODULE} ids_mock_response_loading request_id={request_id} "
                f"path={self.mock_response_path}"
            )
            payload = load_json(self.mock_response_path)
            if not isinstance(payload, dict):
                raise ValueError("IDS mock payload must be a JSON object")
            state = self._parse_ids_payload(payload)
        except Exception as exc:
            logger.error(
                f"{_MODULE} ids_mock_response_failed request_id={request_id} "
                f"path={self.mock_response_path} "
                f"exception_type={type(exc).__name__} error={exc}"
            )
            return IDSDeviceCapabilityState()

        logger.info(
            f"{_MODULE} ids_device_capability_state_loaded request_id={request_id} "
            f"source=mock installed_app_count={len(state.installed_apps)}"
        )
        return state

    def _query_remote_ids(
        self,
        ids_query: IDSHttpRequest,
        request_id: str,
    ) -> dict[str, Any]:
        """真实请求 IDS 查询接口。

        入参：
        - ids_query：结构化 IDS HTTP 请求定义。
        - request_id：本次 IDS 查询请求 ID。
        出参：IDS 原始 JSON 响应；请求失败时返回空 nameSpaces，避免生成流程异常中断。
        """
        # URL 若仍保留 Postman 占位符，说明部署环境还没配置真实 IDS 地址。
        if "{{" in ids_query.url or "}}" in ids_query.url:
            logger.error(
                f"{_MODULE} ids_remote_query_url_not_configured request_id={request_id} "
                f"url={ids_query.url}"
            )
            return {"nameSpaces": []}

        try:
            logger.info(
                f"{_MODULE} ids_remote_query_started request_id={request_id} "
                f"method={ids_query.method} url={ids_query.url} "
                f"timeout_seconds={self.settings.ids_request_timeout_seconds}"
            )
            response = requests.request(
                method=ids_query.method,
                url=ids_query.url,
                json=ids_query.body.model_dump(mode="json"),
                timeout=self.settings.ids_request_timeout_seconds,
                headers=ids_query.headers.model_dump(mode="json", by_alias=True),
                stream=False,
                verify=False,
                allow_redirects=False,
            )
            logger.info(
                f"{_MODULE} ids_remote_query_response_received request_id={request_id} "
                f"status_code={response.status_code} response_bytes={len(response.content)}"
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                logger.error(
                    f"{_MODULE} ids_remote_query_invalid_response_type request_id={request_id} "
                    f"response_type={type(payload).__name__}"
                )
                return {"nameSpaces": []}
            payload = self._validate_business_response(payload, request_id)
            logger.debug(
                f"{_MODULE} ids_remote_query_payload_loaded request_id={request_id} "
                f"namespace_count={len(payload.get('nameSpaces', []))}"
            )
            return payload
        except (requests.RequestException, ValueError) as exc:
            logger.error(
                f"{_MODULE} ids_remote_query_failed request_id={request_id} error={exc} "
                f"exception_type={type(exc).__name__} exception={exc!r} "
                f"traceback={traceback.format_exc()}"
            )
            return {"nameSpaces": []}

    def _describe_ids_error(self, ret_code: Any) -> str:
        """返回 IDS 错误码描述，保留实例方法以便调用方和测试复用。"""
        return describe_ids_error(ret_code)

    def _validate_business_response(
        self,
        payload: dict[str, Any],
        request_id: str,
    ) -> dict[str, Any]:
        """校验 IDS 业务层返回码，并过滤失败的 namespace。"""
        top_level_ret_code = payload.get("retCode")
        if top_level_ret_code is not None and not _is_success_ret_code(top_level_ret_code):
            logger.error(
                f"{_MODULE} ids_business_error request_id={request_id} "
                f"scope=top ret_code={top_level_ret_code} "
                f"description={payload.get('description', '')} "
                f"error_description={self._describe_ids_error(top_level_ret_code)}"
            )
            return {"nameSpaces": []}

        namespaces = payload.get("nameSpaces", [])
        if not isinstance(namespaces, list):
            logger.error(
                f"{_MODULE} ids_invalid_namespaces request_id={request_id} "
                f"response_type={type(namespaces).__name__}"
            )
            return {"nameSpaces": []}

        valid_namespaces: list[dict[str, Any]] = []
        for namespace in namespaces:
            if not isinstance(namespace, dict):
                logger.error(
                    f"{_MODULE} ids_invalid_namespace request_id={request_id} "
                    f"response_type={type(namespace).__name__}"
                )
                continue
            namespace_ret_code = namespace.get("retCode")
            if namespace_ret_code is not None and not _is_success_ret_code(namespace_ret_code):
                logger.error(
                    f"{_MODULE} ids_business_error request_id={request_id} "
                    f"scope=namespace data_type={namespace.get('dataType', '')} "
                    f"ret_code={namespace_ret_code} "
                    f"description={namespace.get('description', '')} "
                    f"error_description={self._describe_ids_error(namespace_ret_code)}"
                )
                continue
            valid_namespaces.append(namespace)

        if len(valid_namespaces) == len(namespaces):
            return payload
        normalized_payload = dict(payload)
        normalized_payload["nameSpaces"] = valid_namespaces
        return normalized_payload

    def _safe_headers_for_log(self, ids_query: IDSHttpRequest) -> dict[str, Any]:
        """生成可打印的 IDS 请求头。

        入参：
        - ids_query：结构化 IDS HTTP 请求定义。
        出参：脱敏后的请求头字典。
        """
        headers = ids_query.headers.model_dump(mode="json", by_alias=True)
        if "idsSign" in headers:
            headers["idsSign"] = f"{headers['idsSign'][:8]}***"
        return headers

    def _parse_ids_payload(self, payload: dict[str, Any]) -> IDSDeviceCapabilityState:
        """解析 IDS 原始响应。

        入参：
        - payload：IDS 原始 JSON 响应。
        出参：转换后的设备能力状态。
        """
        installed_apps: set[str] = set()
        if not isinstance(payload, dict):
            return IDSDeviceCapabilityState()

        top_level_ret_code = payload.get("retCode")
        if top_level_ret_code is not None and not _is_success_ret_code(top_level_ret_code):
            logger.error(
                f"{_MODULE} ids_payload_business_error scope=top "
                f"ret_code={top_level_ret_code} "
                f"description={payload.get('description', '')} "
                f"error_description={self._describe_ids_error(top_level_ret_code)}"
            )
            return IDSDeviceCapabilityState()

        namespaces = payload.get("nameSpaces", [])
        if isinstance(namespaces, list):
            for namespace in namespaces:
                if not isinstance(namespace, dict):
                    continue
                namespace_ret_code = namespace.get("retCode")
                if namespace_ret_code is not None and not _is_success_ret_code(namespace_ret_code):
                    logger.error(
                        f"{_MODULE} ids_payload_business_error scope=namespace "
                        f"data_type={namespace.get('dataType', '')} "
                        f"ret_code={namespace_ret_code} "
                        f"description={namespace.get('description', '')} "
                        f"error_description={self._describe_ids_error(namespace_ret_code)}"
                    )
                    continue
                data_type = namespace.get("dataType", "")
                values = namespace.get("values", [])
                if data_type == "t_ids_kv_ohos_installed_apps":
                    installed_apps.update(self._collect_installed_apps(values))

        installed_apps.update(self._collect_result_set_apps(payload.get("resultSets")))

        logger.debug(
            f"{_MODULE} ids_payload_parsed installed_app_count={len(installed_apps)}"
        )
        return IDSDeviceCapabilityState(installed_apps=installed_apps)

    def _collect_installed_apps(self, values: Any) -> set[str]:
        """从 IDS values 中收集已安装应用。

        入参：
        - values：安装应用 namespace 下的 values 列表。
        出参：已安装应用包名集合。
        """
        installed_apps: set[str] = set()
        if not isinstance(values, list):
            return installed_apps
        for value in values:
            if not isinstance(value, dict):
                continue
            data = value.get("data", {})
            if not isinstance(data, dict):
                continue
            bundle_name = data.get("bundleName")
            if isinstance(bundle_name, str) and bundle_name:
                installed_apps.add(bundle_name)
        return installed_apps

    def _collect_result_set_apps(self, result_sets: Any) -> set[str]:
        """兼容旧版 resultSets/dataValue 响应，提取明确的 bundleName 字段。"""
        installed_apps: set[str] = set()
        if not isinstance(result_sets, list):
            return installed_apps
        for result_set in result_sets:
            if not isinstance(result_set, dict):
                continue
            data_value = result_set.get("dataValue")
            if isinstance(data_value, str):
                try:
                    data_value = json.loads(data_value)
                except (TypeError, ValueError):
                    logger.warning(
                        f"{_MODULE} ids_result_set_data_value_invalid "
                        f"data_type={type(data_value).__name__}"
                    )
                    continue
            if isinstance(data_value, dict):
                bundle_name = data_value.get("bundleName")
                if isinstance(bundle_name, str) and bundle_name:
                    installed_apps.add(bundle_name)
                installed_apps.update(self._collect_installed_apps([data_value]))
            elif isinstance(data_value, list):
                for item in data_value:
                    if not isinstance(item, dict):
                        continue
                    bundle_name = item.get("bundleName")
                    if isinstance(bundle_name, str) and bundle_name:
                        installed_apps.add(bundle_name)
                    installed_apps.update(self._collect_installed_apps([item]))
        return installed_apps
