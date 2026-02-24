import asyncio
import sys
import time
from typing import Optional

import requests

try:
    import winrt.windows.data.xml.dom as dom
    import winrt.windows.ui.notifications as notifications
    import winrt.windows.ui.notifications.management as management
except ImportError:
    print(
        "Error: Required WinRT modules not found.\n"
        "Run: pip install winrt-runtime "
        "winrt-Windows.UI.Notifications "
        "winrt-Windows.UI.Notifications.Management "
        "winrt-Windows.Foundation "
        "winrt-Windows.Data.Xml.Dom"
    )
    sys.exit(1)

_processed_ids: set = set()
_last_signature: Optional[str] = None
_last_timestamp: float = 0.0


def send_to_telegram(config: dict, title: str, text: str, app_name: str) -> None:
    token = config["telegram_bot_token"]
    chat_id = config["telegram_chat_id"]
    message = (
        f"\U0001f514 *New Notification*\n\n"
        f"*App:* {app_name}\n"
        f"*Title:* {title}\n"
        f"*Message:* {text}"
    )
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"Failed to send to Telegram: {response.text}", flush=True)
    except Exception as e:
        print(f"Error sending to Telegram: {e}", flush=True)


def _make_handler(config: dict):
    def handler(listener, event_args):
        global _last_signature, _last_timestamp

        try:
            kind = getattr(event_args, "change_kind", None)
            if kind is None:
                kind = getattr(event_args, "change_type", None)
            if kind is not None and kind != 0:
                return

            notif_id = event_args.user_notification_id
            if notif_id in _processed_ids:
                return

            notification = listener.get_notification(notif_id)
            if not notification:
                return

            try:
                app_name = notification.app_info.display_info.display_name
            except Exception:
                app_name = "Unknown App"

            visual = notification.notification.visual
            title, text = "Notification", ""
            for binding in visual.bindings:
                elems = binding.get_text_elements()
                if len(elems) > 0:
                    title = elems[0].text
                if len(elems) > 1:
                    text = " ".join(el.text for el in elems[1:])

            signature = f"{app_name}|{title}|{text}"
            now = time.time()
            if signature == _last_signature and (now - _last_timestamp) < 5.0:
                return

            _processed_ids.add(notif_id)
            _last_signature = signature
            _last_timestamp = now

            if len(_processed_ids) > 100:
                _processed_ids.pop()

            print(f"Forwarding: [{app_name}] {title}", flush=True)
            send_to_telegram(config, title, text, app_name)

        except Exception as e:
            print(f"Error in handler: {e}", flush=True)

    return handler


async def run(config: dict, stop_event: Optional[asyncio.Event] = None) -> None:
    from .config import clear_pid, write_pid

    write_pid()
    try:
        print("Starting OS Notification Forwarder...")

        listener = management.UserNotificationListener.current
        access_status = await listener.request_access_async()

        if access_status != management.UserNotificationListenerAccessStatus.ALLOWED:
            print(
                "Error: Notification access denied.\n"
                "Go to: Settings > Privacy & security > Notifications\n"
                "and allow access for your terminal / Python."
            )
            return

        listener.add_notification_changed(_make_handler(config))
        print("Listening for notifications. Press Ctrl+C to stop.")

        while True:
            if stop_event is not None and stop_event.is_set():
                break
            await asyncio.sleep(1)

    finally:
        clear_pid()


def send_test_notification() -> None:
    toast_xml = (
        "<toast>"
        "<visual><binding template='ToastGeneric'>"
        "<text>os-notif-telegram</text>"
        "<text>Test notification! Check your Telegram.</text>"
        "</binding></visual>"
        "</toast>"
    )
    xml_doc = dom.XmlDocument()
    xml_doc.load_xml(toast_xml)
    notif = notifications.ToastNotification(xml_doc)
    notifier = notifications.ToastNotificationManager.create_toast_notifier()
    notifier.show(notif)
    print("Test notification sent! Check your Telegram.")
