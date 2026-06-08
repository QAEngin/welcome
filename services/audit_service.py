import csv
import io
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

try:
    from google.cloud import logging as cloud_logging
except ImportError:  # pragma: no cover - optional runtime dependency
    cloud_logging = None


AUDIT_LOGGER_NAME = "sms_manager.audit"


class AuditService:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(AUDIT_LOGGER_NAME)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            self.logger.addHandler(logging.StreamHandler())

    def write_event(
        self,
        action: str,
        status: str,
        actor_email: str = "",
        actor_uid: str = "",
        target_email: str = "",
        target_uid: str = "",
        source: str = "app",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor_email": actor_email,
            "actor_uid": actor_uid,
            "target_email": target_email,
            "target_uid": target_uid,
            "action": action,
            "status": status,
            "source": source,
            "metadata": metadata or {},
        }
        self.logger.info(json.dumps(event, ensure_ascii=True))
        self._append_local_event(event)
        return event

    def _append_local_event(self, event: dict[str, Any]) -> None:
        path = self.config.audit_log_file
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=True) + "\n")

    def list_events(
        self,
        actor: str = "",
        action: str = "",
        start_date: str = "",
        end_date: str = "",
        max_results: int = 200,
    ) -> list[dict[str, Any]]:
        local_events = self._read_local_events(actor, action, start_date, end_date)
        cloud_events = self._read_cloud_events(actor, action, start_date, end_date)
        merged = sorted(local_events + cloud_events, key=lambda item: item.get("timestamp", ""), reverse=True)
        return merged[:max_results]

    def _read_local_events(self, actor: str, action: str, start_date: str, end_date: str) -> list[dict[str, Any]]:
        path = self.config.audit_log_file
        if not os.path.exists(path):
            return []
        results = []
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not _match_filters(event, actor, action, start_date, end_date):
                    continue
                results.append(event)
        return results

    def _read_cloud_events(self, actor: str, action: str, start_date: str, end_date: str) -> list[dict[str, Any]]:
        if cloud_logging is None or not self.config.identity_platform_project_id:
            return []
        try:
            client = cloud_logging.Client(project=self.config.identity_platform_project_id)
        except Exception:
            return []

        filters = [
            'resource.type="cloud_run_revision" OR resource.type="audited_resource"',
            '(logName:"run.googleapis.com" OR logName:"identitytoolkit.googleapis.com" OR jsonPayload.action:*)',
        ]
        if start_date:
            filters.append(f'timestamp>="{start_date}T00:00:00Z"')
        if end_date:
            filters.append(f'timestamp<="{end_date}T23:59:59Z"')
        filter_expression = " AND ".join(filters)

        exported = []
        try:
            iterator = client.list_entries(filter_=filter_expression, page_size=100)
            for entry in iterator:
                event = _normalize_cloud_entry(entry)
                if not event:
                    continue
                if not _match_filters(event, actor, action, start_date, end_date):
                    continue
                exported.append(event)
                if len(exported) >= 200:
                    break
        except Exception:
            return []
        return exported

    def export_csv(self, events: list[dict[str, Any]]) -> io.BytesIO:
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=["timestamp", "actor_email", "actor_uid", "target_email", "target_uid", "action", "status", "source", "metadata"],
        )
        writer.writeheader()
        for event in events:
            row = dict(event)
            row["metadata"] = json.dumps(row.get("metadata") or {}, ensure_ascii=False)
            writer.writerow(row)

        data = io.BytesIO(output.getvalue().encode("utf-8-sig"))
        data.seek(0)
        return data


def _normalize_cloud_entry(entry) -> dict[str, Any] | None:
    payload = getattr(entry, "payload", None) or {}
    timestamp = getattr(entry, "timestamp", None)
    ts = timestamp.isoformat() if timestamp else ""
    if isinstance(payload, dict) and payload.get("action"):
        return {
            "timestamp": ts,
            "actor_email": payload.get("actor_email", ""),
            "actor_uid": payload.get("actor_uid", ""),
            "target_email": payload.get("target_email", ""),
            "target_uid": payload.get("target_uid", ""),
            "action": payload.get("action", ""),
            "status": payload.get("status", ""),
            "source": payload.get("source", "cloud"),
            "metadata": payload.get("metadata", {}),
        }

    proto = getattr(entry, "proto_payload", None)
    if proto:
        metadata = {
            "service_name": getattr(proto, "service_name", ""),
            "method_name": getattr(proto, "method_name", ""),
        }
        principal_email = getattr(getattr(proto, "authentication_info", None), "principal_email", "")
        action = metadata["method_name"] or getattr(proto, "service_name", "cloud.audit")
        return {
            "timestamp": ts,
            "actor_email": principal_email,
            "actor_uid": "",
            "target_email": "",
            "target_uid": "",
            "action": action,
            "status": "ok",
            "source": metadata["service_name"] or "cloud.audit",
            "metadata": metadata,
        }
    return None


def _match_filters(event: dict[str, Any], actor: str, action: str, start_date: str, end_date: str) -> bool:
    actor = actor.strip().lower()
    action = action.strip().lower()
    if actor:
        actor_fields = f'{event.get("actor_email", "")} {event.get("target_email", "")}'.lower()
        if actor not in actor_fields:
            return False
    if action and action not in str(event.get("action", "")).lower():
        return False
    event_ts = event.get("timestamp", "")
    if start_date and event_ts and event_ts < f"{start_date}T00:00:00":
        return False
    if end_date and event_ts and event_ts > f"{end_date}T23:59:59":
        return False
    return True
