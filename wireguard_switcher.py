#!/usr/bin/env python3
import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer

# === CONFIGURATION ===
WG_INTERFACES = ["Sys76Laptop_Ads", "Sys76Laptop"]  # Update with your interfaces
ICON_ON = "🟢"
ICON_OFF = "🔴"


def run_command(cmd):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def is_vpn_up(interface):
    result = run_command(["sudo", "wg", "show", interface])
    return result.returncode == 0 and b"interface" in result.stdout


def notify(title, message):
    subprocess.run(["notify-send", title, message])


def get_ip():
    try:
        return (
            subprocess.check_output(["curl", "-s", "https://ifconfig.me"], timeout=2)
            .decode()
            .strip()
        )
    except:
        return "unknown"


def disable_all_except(selected_iface):
    for iface in WG_INTERFACES:
        if iface != selected_iface and is_vpn_up(iface):
            run_command(["sudo", "wg-quick", "down", iface])
            notify(f"WireGuard [{iface}]", "VPN disconnected")


def toggle_vpn(interface, tray, actions):
    if is_vpn_up(interface):
        run_command(["sudo", "wg-quick", "down", interface])
        notify(f"WireGuard [{interface}]", "VPN disconnected")
    else:
        disable_all_except(interface)
        run_command(["sudo", "wg-quick", "up", interface])
        notify(f"WireGuard [{interface}]", "VPN connected")
    update_menu(actions, tray)


def get_overall_icon(interface_states):
    if any(state == "ON" for state in interface_states.values()):
        return QIcon.fromTheme("network-vpn")  # Or use a custom icon path
    else:
        return QIcon.fromTheme("network-offline")


def update_menu(actions, tray):
    interface_states = {}

    # Update each menu item and track state
    for iface, action in actions.items():
        if is_vpn_up(iface):
            status = "ON"
            emoji = ICON_ON
        else:
            status = "OFF"
            emoji = ICON_OFF
        action.setText(f"{emoji} {iface}: {status}")
        interface_states[iface] = status

    # Tooltip with status and IP
    ip = get_ip()
    tooltip_lines = [f"{iface}: {status}" for iface, status in interface_states.items()]
    tooltip_text = "WireGuard VPNs:\n" + "\n".join(tooltip_lines) + f"\nIP: {ip}"
    tray.setToolTip(tooltip_text)

    # Icon based on active VPNs
    tray.setIcon(get_overall_icon(interface_states))


def main():
    app = QApplication(sys.argv)
    tray = QSystemTrayIcon()
    tray.setIcon(QIcon.fromTheme("network-offline"))
    tray.setToolTip("WireGuard Tray")
    tray.show()

    menu = QMenu()
    interface_actions = {}

    for iface in WG_INTERFACES:
        action = QAction()
        action.triggered.connect(
            lambda checked, i=iface: toggle_vpn(i, tray, interface_actions)
        )
        interface_actions[iface] = action
        menu.addAction(action)

    # menu.addSeparator()
    # quit_action = QAction("Quit")
    # quit_action.triggered.connect(app.quit)
    # menu.addAction(quit_action)

    tray.setContextMenu(menu)

    # Update tray every 10 seconds
    timer = QTimer()
    timer.timeout.connect(lambda: update_menu(interface_actions, tray))
    timer.start(10000)

    update_menu(interface_actions, tray)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
