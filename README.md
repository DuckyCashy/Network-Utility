# Network Utility CLI Tool

A multi-threaded network diagnostics, scanning, and identification utility built natively in Python. This tool gives you insight into your local subnet architecture, profiles active devices by operating system type, and provides quick administrative configuration overrides for network adapters. (Formerly IPChecker)

---

## 🚀 Getting Started & Prerequisites

To utilize all features of Network Utility, it must be executed inside a terminal session with administrative permissions.

* **Windows:** Right-click your Terminal/Command Prompt and select **"Run as Administrator"**.
* **Linux/macOS:** Run the script prefixed with `sudo` (e.g., `sudo python ip_network.py`).

If you forget, you can quickly run the built-in elevator using Option `[5]`.

---

## 🛠️ Detailed Option Guide & Descriptions

### [1] Get Local IP
* **Description:** Pinpoints your machine's actual primary IP address on the local network. Unlike static environment variable reads, it initializes a live low-overhead UDP dummy socket connection out to an external gateway to determine exactly which interface card is routing traffic.
* **How to Use:** 1. Select Option `1`.
  2. The console will display your active assignment (e.g., `[SUCCESS] Local IP Found: 123.456.7.89`).

---

### [2] Scan Subnet & Profile Devices
* **Description:** Runs an active discovery scan across your entire subnet (`.1` to `.254`). To bypass aggressive firewalls that block standard pings, it uses system-level hooks to build an ARP map. Once a device's physical MAC address responds, it fingerprints active operating system ports.
* **Classifications Detected:**
  * `PC (Windows)` via Ports 135/445
  * `PC (MacOS)` via Ports 548/5900
  * `Mobile (iOS Device)` via Apple Lockdown Port 62078
  * `Mobile (Android Device)` via ADB Port 5555
  * `PC (ChromeOS Device)` via Ports 9222/2222
  * `PC / Server (Linux)` via Port 22
  * `[YOUR PC]` dynamically appended next to your own machine's signature.
* **How to Use:**
  1. Select Option `2`.
  2. Wait a few seconds for the multi-threaded cycle to resolve all 254 endpoints.
  3. Review the live matrix printing IP, MAC, and device type.

---

### [3] Rotate/Obfuscate Network IP
* **Description:** Breaks your network's standard automatic configuration loop by bypassing your router's DHCP lease. It forcefully sets a manual static configuration on your Windows network interface, instantly shifting your host identification to an alternate zone (e.g., swapping to `.150` or `.50`).
* **Built-in Safe Toggle:** If the script detects that your IP is already obfuscated, running this option again will prompt: `"IP has already been Obfuscated. Would you like to disable it? (y/n)"`. Selecting `y` immediately restores your network adapter to automatic DHCP control.
* **How to Use:**
  1. Ensure you are running as **Administrator**.
  2. Select Option `3` to toggle the static obfuscation on.
  3. When you are finished and want normal internet access back, select Option `3` again and type `y` to disable it.

---

### [4] IP Forwarding
* **Description:** Modifies low-level kernel routing variables (`net.ipv4.ip_forward` on Unix systems or `IPEnableRouter` in the Windows Registry) and initializes a background routing loop thread. It handles standard redirection pipelines between targets and default gateways.
* **How to Use:**
  1. Select Option `4`.
  2. Type in the target IP address you wish to point or forward traffic from when prompted.
  3. Run Option `4` a second time to safely terminate the routing loops and stand down the background interface thread.

---

### [5] Relaunch as Administrator
* **Description:** A quick shortcut designed to elevate your current terminal context. If your console is running under a limited user profile, choosing this option triggers the OS native elevation mechanism (`ShellExecuteW` via ctypes on Windows or a `sudo` sub-execution shell on UNIX) to securely pass runtime flags over to an advanced clearance terminal.
* **How to Use:** Select Option `5` and accept the operating system's administrative/UAC prompt.

---

### [6] Close Terminal
* **Description:** Terminates all operational background threads, stops active hooks safely, and completely shuts down the application runtime cleanly.
* **How to Use:** Select Option `6`.

---

## 🤫 Secret Commands

* **`revert`**: Type this into the main selection prompt while running in Administrator mode to drop your clearance tier down and quickly relaunch a standard, limited user terminal instance.
* **`github`**: Type this into the main selection prompt to automatically open the project source repository in your system browser.
