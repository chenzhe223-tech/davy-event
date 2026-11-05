from davy_event import normalize_event, verify_event, export_events

raw = {
    "活动名称": "周末亲子创意工作坊",
    "开始时间": "2026-11-07T10:00:00+08:00",
    "地址": "Singapore",
    "原文链接": "https://example.org/public-event"
}

event = verify_event(normalize_event(raw, source="user_supplied"))
print(export_events([event]))
