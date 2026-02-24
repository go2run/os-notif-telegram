"""System tray icon for os-notif-telegram."""

import asyncio
import threading

import pystray
from PIL import Image, ImageDraw


def _create_icon_image() -> Image.Image:
    """Draw a simple blue circle with a bell silhouette."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Blue circle background
    d.ellipse([0, 0, size - 1, size - 1], fill="#2196F3")

    # Bell body
    d.ellipse([16, 14, 48, 44], fill="white")
    d.rectangle([16, 28, 48, 46], fill="white")

    # Bell base
    d.rectangle([12, 44, 52, 50], fill="white", outline="white")

    # Clapper
    d.ellipse([26, 48, 38, 56], fill="white")

    # Bell top (stem)
    d.rectangle([29, 8, 35, 16], fill="white")
    d.ellipse([26, 6, 38, 16], fill="white")

    return img


def run_with_tray(config: dict) -> None:
    """Run the forwarder with a system tray icon.

    The asyncio loop runs in a background thread.
    The tray icon runs on the main thread (required on Windows).
    Closing the tray icon or clicking Stop will cleanly shut down the forwarder.
    """
    from .forwarder import run as forwarder_run

    loop = asyncio.new_event_loop()
    stop_event = asyncio.Event()

    def _run_loop() -> None:
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(forwarder_run(config, stop_event))
        finally:
            loop.close()

    thread = threading.Thread(target=_run_loop, daemon=True)
    thread.start()

    def on_stop(icon: pystray.Icon, _item) -> None:
        loop.call_soon_threadsafe(stop_event.set)
        icon.stop()

    icon = pystray.Icon(
        name="os-notif-telegram",
        icon=_create_icon_image(),
        title="os-notif-telegram: Forwarding...",
        menu=pystray.Menu(
            pystray.MenuItem("Forwarding notifications", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Stop", on_stop),
        ),
    )

    try:
        icon.run()  # Blocks on the main thread until icon.stop() is called
    finally:
        # Ensure the asyncio loop stops if the tray is dismissed any other way
        loop.call_soon_threadsafe(stop_event.set)
        thread.join(timeout=3)
