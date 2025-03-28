#  simple example.py must be provided to explain how your function is used
# from ping_subnets.main import main

from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import subprocess
import logging

def ping_ip(ip_addr, retries, n):
    """
    Pings an IP address and returns success status.

    Args:
        ip_addr (str): The IP address to ping.
        retries (int): Number of retry attempts.
        n (int): Additional identifier (optional, not used here).

    Returns:
        tuple: (ip_addr, bool) -> IP address and ping success status.
    """
    for attempt in range(retries + 1):
        try:
            result = subprocess.run(
                ["ping", "-c", "1", ip_addr],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False
            )
            return ip_addr, result.returncode == 0
        except Exception as e:
            logging.warning(f"Attempt {attempt + 1}: Exception occurred while pinging {ip_addr}: {e}")
        logging.warning(f"Attempt {attempt + 1} failed for {ip_addr}. Retrying...")
    return ip_addr, False


def ping_subnet(ips, retries, n):
    """
    Pings a list of IP addresses concurrently and returns their results.

    Args:
        ips (list): List of IP addresses to ping.
        retries (int): Number of retry attempts for each IP address.
        n (int): Additional identifier (optional).

    Returns:
        dict: A dictionary with IP addresses as keys and boolean values indicating success.
    """
    results = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_ip = {executor.submit(ping_ip, ip, retries, n): ip for ip in ips}

        # Add tqdm to show progress
        for future in tqdm(as_completed(future_to_ip), total=len(future_to_ip), desc="Pinging IPs"):
            ip, success = future.result()
            results[ip] = success

    return results


if __name__ == "__main__":
    # Example list of IP addresses to ping
    ip_list = [f"192.168.1.{i}" for i in range(1, 21)]  # IPs from 192.168.1.1 to 192.168.1.20
    ip_list = ["192.168.1.0", "8.8.8.8", "127.0.0.1", ]
    retries = 2  # Number of retry attempts

    print("Starting to ping subnet...")
    results = ping_subnet(ip_list, retries, 0)

    # Display the results
    print("\nPing Results:")
    for ip, status in results.items():
        print(f"{ip}: {'Reachable' if status else 'Unreachable'}")
