# IPChecker

IPChecker is a program that is related to IP Stuff. This program is lightweight, cross-platform terminal utility written in Python for network diagnostics, subnet device discovery, and localized routing configuration. It operates seamlessly across Windows, Linux, and macOS environments.

---

## 📖 About

**IPChecker** serves as a centralized network toolkit designed for users who need to analyze and manipulate local network parameters quickly without administrative access to the network router. 

### Key Features:
* **Dynamic Identity Display:** Automatically adapts to permissions, displaying your system user profile or full administrative clearance upon launch.
* **Subnet Profiling:** Scans the active subnet via multi-threaded validation and accurately classifies target devices (e.g., Windows PCs, Linux/macOS servers, or mobile devices) using TTL heuristic metrics.
* **Interface Obfuscation:** Cycles and forces a DHCP lease renewal to dynamically request a fresh local IP assignment from your access point.
* **Standalone IP Forwarding Engine:** Routes and intercepts target machine traffic natively using built-in, low-level socket structures—**requiring zero external third-party dependencies** like Scapy.

---

## 🚀 Guides

### 📋 Prerequisites
Before running the script, ensure you have Python 3.x installed on your computer. 
* **Windows:** Ensure Python is added to your system `PATH`.
* **Linux / macOS:** Python 3 is typically installed by default. You will need a terminal with `sudo` access to unlock administrative features (Options 3 & 4).

---

### 💻 Installation & Setup

1. **Clone or Download the Repository:**
   ```bash
   git clone [https://github.com/DuckyCashy/IPChecker.git](https://github.com/DuckyCashy/IPChecker.git)
   cd IPChecker
