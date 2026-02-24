import asyncio
import os
import signal
import sys

import click

from . import __version__
from .config import (
    clear_pid,
    get_config_path,
    get_running_pid,
    is_configured,
    load_config,
    save_config,
)


@click.group()
@click.version_option(__version__, prog_name="os-notif-telegram")
def main():
    """Forward OS notifications to Telegram."""


@main.command()
@click.option("--token", default=None, help="Telegram bot token (skip prompt)")
@click.option("--chat-id", default=None, help="Telegram chat ID (skip prompt)")
def setup(token, chat_id):
    """Configure your Telegram bot token and chat ID."""
    existing = load_config()

    if token is None:
        current = existing.get("telegram_bot_token", "")
        hint = f" (current: {current[:4]}...{current[-4:]})" if current else ""
        token = click.prompt(
            f"Telegram Bot Token{hint}", default=current or "", show_default=False
        )

    if chat_id is None:
        current = existing.get("telegram_chat_id", "")
        hint = f" (current: {current})" if current else ""
        chat_id = click.prompt(
            f"Telegram Chat ID{hint}", default=current or "", show_default=False
        )

    if not token or not chat_id:
        click.echo("Error: Both token and chat ID are required.", err=True)
        sys.exit(1)

    save_config(
        {"telegram_bot_token": token.strip(), "telegram_chat_id": str(chat_id).strip()}
    )
    click.echo(f"Config saved to: {get_config_path()}")


@main.command("config")
def show_config():
    """Show the current configuration."""
    cfg = load_config()
    if not is_configured(cfg):
        click.echo("Not configured. Run 'os-notif-telegram setup' first.")
        return
    token = cfg["telegram_bot_token"]
    masked = f"{token[:4]}...{token[-4:]}"
    click.echo(f"Config file : {get_config_path()}")
    click.echo(f"Bot Token   : {masked}")
    click.echo(f"Chat ID     : {cfg['telegram_chat_id']}")


@main.command()
@click.option(
    "--no-tray",
    is_flag=True,
    help="Run in terminal instead of minimising to the system tray.",
)
def start(no_tray):
    """Start forwarding notifications to Telegram.

    By default the program minimises to the system tray so you can close the
    terminal window. Use --no-tray to keep it in the foreground instead.
    """
    cfg = load_config()
    if not is_configured(cfg):
        click.echo(
            "Error: Not configured. Run 'os-notif-telegram setup' first.", err=True
        )
        sys.exit(1)

    pid = get_running_pid()
    if pid is not None:
        click.echo(f"Forwarder is already running (PID {pid}).")
        sys.exit(1)

    if no_tray:
        from .forwarder import run

        try:
            asyncio.run(run(cfg))
        except KeyboardInterrupt:
            click.echo("\nStopped.")
    else:
        # 產生一個分離的背景子程序來跑 tray，讓終端機立刻返回
        import subprocess

        _DETACHED_PROCESS = 0x00000008
        _CREATE_NO_WINDOW = 0x08000000

        proc = subprocess.Popen(
            [sys.executable, "-m", "os_notif_telegram", "_worker"],
            creationflags=_DETACHED_PROCESS | _CREATE_NO_WINDOW,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
        click.echo(f"Started in background (PID {proc.pid}). Check the system tray.")


@main.command()
def stop():
    """Stop the running forwarder."""
    pid = get_running_pid()
    if pid is None:
        click.echo("Forwarder is not running.")
        return
    try:
        os.kill(pid, signal.SIGTERM)
        clear_pid()
        click.echo(f"Stopped forwarder (PID {pid}).")
    except Exception as e:
        click.echo(f"Error stopping forwarder: {e}", err=True)
        sys.exit(1)


@main.command()
def status():
    """Show whether the forwarder is currently running."""
    pid = get_running_pid()
    if pid:
        click.echo(f"Running (PID {pid})")
    else:
        click.echo("Not running")


@main.command("_worker", hidden=True)
def worker():
    """Internal: runs the tray icon in the detached background process."""
    cfg = load_config()
    if not is_configured(cfg):
        sys.exit(1)
    from .tray import run_with_tray

    run_with_tray(cfg)


@main.command()
def test():
    """Send a test notification to verify Telegram forwarding.

    Make sure 'os-notif-telegram start' is running first.
    """
    cfg = load_config()
    if not is_configured(cfg):
        click.echo(
            "Error: Not configured. Run 'os-notif-telegram setup' first.", err=True
        )
        sys.exit(1)

    from .forwarder import send_test_notification

    send_test_notification()
