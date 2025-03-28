"""
A product your team is designing has multiple devices that
communicate with each other using ethernet networks.
For redundancy, there are 2 networks for each device.
You are responsible for writing a Python library that
provides a function which returns a list of IP addresses
that are pingable on one network but not the other.
We will review your code the same as we would review
any pull request at Joby and want to see you give us your
best in performance and style! We will set the review up
to be anonymous to ensure an unbiased review of your submission.
"""
import ipaddress
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import sys
from tqdm import tqdm

# Configure the logger
logging.basicConfig(
    level=logging.INFO,  # Set the logging level to INFO
    # Define the log message format
    format='%(asctime)s - [%(funcName)s:%(lineno)d] '\
           '- %(levelname)s - %(message)s')
CIDR = 30


def check_retries(retries: int)->int:
    """
    Validates the number of retries and ensures it is within the range [1, 3].

    If the input `retries` is outside the allowed range, a warning is logged,
    and the function defaults the value to 1.

    Args:
        retries (int): The number of retries to validate.

    Returns:
        int: A valid number of retries (1, 2, or 3).

    Logs:
        Warning: If `retries` is not between 1 and 3.
    """
    if not 1 <= retries <= 3:
        logging.warning("Retries must be between 1 and 3. Defaulting to 1.")
        return 1
        # raise ValueError("Retries must be between 1 and 3.")
    return retries


def validate_subnet(subnet)->bool:
    """
    Validates the subnet and ensures it has correct CIDR notation value.

    This function performs the following:
    - Validates that the CIDR notation is valid.
    - Logs a warning for CIDR values not equal to 24, will return False.
    - Logs warning for subnets that have host bits set, returns False.

    Args:
        subnet (str): The IPv4 subnet in CIDR notation
        (e.g., '192.168.1.0/24').

    Returns:
        bool: True or False value

    Raises:
        ValueError: If any entry in the ignore_list is not an integer.
        ValueError: If the subnet is invalid or not in CIDR notation.

    Example:
        >>> subnet = "192.168.1.0/30"
        >>> ignore_list = [1, 2]
        >>> validate_ignore_list(subnet, ignore_list)
        ['192.168.1.3']
    """
    try:
        network = ipaddress.IPv4Network(subnet, strict=True)
        if network.prefixlen != CIDR:
            logging.warning("(%s): Only /24 subnets are allowed.", subnet)
            return False
            # raise ValueError("Only /24 subnets are allowed.")
        return True
    except ValueError as error:
        logging.warning("Invalid subnet '{%s}': {%s}", subnet, error)
        # raise ValueError(f"Invalid subnet '{subnet}': {e}")
        return False


def validate_ignore_list(subnet, ignore_list)->list:
    """
    Validates the ignore_list for a given subnet.

    This function performs the following:
    - Validates that the ignore_list contains valid integers.
    - Logs a warning for any octet in the ignore_list that is
    out of range (0-255).
    - Generates all valid host IPs for the given subnet
    (excluding network and broadcast addresses).
    - Filters out any IPs whose last octet matches values in the ignore_list.

    Args:
        subnet (str): The IPv4 subnet in CIDR notation
        (e.g., '192.168.1.0/24'). ignore_list (list[int]):
        A list of octets to be excluded from the subnet.

    Returns:
        list[str]: A list of filtered IP addresses as strings.

    Raises:
        ValueError: If any entry in the ignore_list is not an integer.
        ValueError: If the subnet is invalid or not in CIDR notation.

    Example:
        >>> subnet = "192.168.1.0/30"
        >>> ignore_list = [1, 2]
        >>> validate_ignore_list(subnet, ignore_list)
        ['192.168.1.3']
    """
    # Validate that all elements in ignore_list are integers
    if not all(isinstance(octet, int) for octet in ignore_list):
        raise ValueError("All entries in ignore_list must be integers.")

    # Check for out-of-range octets and log warnings
    for octet in ignore_list:
        if octet < 0 or octet > 255:
            logging.warning("Octet {%s} in ignore_list is out of range "
                            "(0-255).", octet)

    # Generate all IPs in the subnet
    network = ipaddress.IPv4Network(subnet, strict=True)
    # network_address = network.network_address
    # broadcast_address = network.broadcast_address

    # Generate all IPs in the subnet
    # .hosts() excludes the network and broadcast by default
    subnet_ips = list(network.hosts())
    # subnet_ips = list(network)

    # Filter out IPs with last octet in ignore_list
    filtered_ips = [
        str(ip) for ip in subnet_ips
        if ip.packed[-1] not in ignore_list
    ]
    return filtered_ips


def ping_ip(ip_addr, retries):
    """
    Pings a given IP address a specified number of
    times and returns the result.

    This function attempts to ping the provided IP address
    for a number of retries. If the ping is successful, it
    returns the IP address along with `True`. If the ping
    fails or an exception occurs, it returns the IP address
    with `False`. It also logs warnings for failed attempts
    or exceptions during the ping process.

    Args:
        ip_addr (str): The IP address to ping.
        retries (int): The number of retries to attempt
        if the ping fails.
        n (int): An additional parameter
        (not currently used in the function, can be
        used for future extensions).

    Returns:
        tuple: A tuple containing:
            - The IP address (`ip_addr`).
            - A boolean value (`True` if the ping
            is successful, `False` otherwise).

    Logs:
        Warning: If a ping attempt fails, or if an
        exception occurs during the ping process.

    Example:
        ip = "192.168.1.1"
        retries = 3
        result = ping_ip(ip, retries, 0)
        print(result)  # Output: ("192.168.1.1", True) if
        ping is successful, else ("192.168.1.1", False)
    """
    for attempt in range(retries+1):
        try:
            result = subprocess.run(
                ["ping", "-c", "1", ip_addr],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False
            )
            # True if ping is successful
            return ip_addr, result.returncode == 0
        except Exception as error:
            logging.warning(
                "Attempt %s: Exception occurred while pinging %s: %s",
                (attempt+1), ip_addr, error)
            # return ip, False  # Return False on exception

        logging.warning("Attempt %s failed for %s. Retrying...",
                        (attempt+1), ip_addr)
    return ip_addr, False  # Return False on exception

    #  Example: Simulate pingable if last octet is even
    # if n == 0:
    #     return ip, int(ip.split(".")[-1]) % 2 == 0
    # else:
    #     return ip, int(ip.split(".")[-1]) % 2 == 1


def ping_subnet(ips, retries)->dict:
    """
    Pings a list of IP addresses concurrently using a thread pool.

    This function sends a ping request to each IP address in the
    provided list (`ips`), retrying up to the specified
    number of times (`retries`) if the ping fails. The function
    uses a thread pool to perform the pings concurrently
    for improved efficiency.

    Args:
        ips (list of str): A list of IP addresses to ping.
        retries (int): The number of retries to attempt if
        a ping fails.
        n (int): A parameter passed to the `ping_ip` function
        (its purpose should be documented in `ping_ip`).

    Returns:
        dict: A dictionary where the keys are the IP addresses
        and the values are boolean values indicating
        whether the ping was successful (`True`) or failed (`False`).

    Example:
        ips = ["192.168.1.1", "192.168.1.2"]
        retries = 3
        n = 5
        result = ping_subnet(ips, retries, n)
        print(result)
        # Output: {"192.168.1.1": True, "192.168.1.2": False}
    """
    results = {}

    # Adjust max_workers as needed
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_ip = {executor.submit(ping_ip, ip_addr, retries):
                        ip_addr for ip_addr in ips}
        # for future in as_completed(future_to_ip):
        for future in tqdm(as_completed(future_to_ip),
                           total=len(future_to_ip), desc="Pinging IPs"):
            ip_addr, success = future.result()
            results[ip_addr] = success
    return results


def ping_both_subnets(ips_1: str, ips_2: str,
                      retries: int):
    """
    Pings two different subnets concurrently and returns the
    results for each.

    This function sends ping requests to the IP addresses in two
    separate subnets (`ips_1` and `ips_2`) concurrently using
    a thread pool. Each subnet is pinged independently, and the
    results for both are returned once all pings are complete.

    Args:
        ips_1 (str): A list of IP addresses for the first subnet to ping.
        ips_2 (str): A list of IP addresses for the second subnet to ping.
        retries (int): The number of retries to attempt if a ping fails.

    Returns:
        tuple: A tuple containing two dictionaries:
            - The first dictionary contains the ping results
            for the first subnet (`ips_1`).
            - The second dictionary contains the ping results
            for the second subnet (`ips_2`).

        Each dictionary has IP addresses as keys and boolean
        values indicating whether the ping was
        successful (`True`) or failed (`False`).

    Example:
        ips_1 = ["192.168.1.1", "192.168.1.2"]
        ips_2 = ["192.168.2.1", "192.168.2.2"]
        retries = 3
        result_subnet1, result_subnet2 =
        ping_both_subnets(ips_1, ips_2, retries)
        print(result_subnet1)  # Output:
        {"192.168.1.1": True, "192.168.1.2": False}
        print(result_subnet2)  # Output:
        {"192.168.2.1": True, "192.168.2.2": True}
    """

    # Parallelize across two subnets
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_subnet1 = executor.submit(ping_subnet, ips_1, retries)
        future_subnet2 = executor.submit(ping_subnet, ips_2, retries)

        # Collect results
        results_subnet1 = future_subnet1.result()
        results_subnet2 = future_subnet2.result()

    return results_subnet1, results_subnet2


def main(subnet1: str, subnet2: str, retries: int = 1, ignore_list: list = []):
    """
    Main function to ping two subnets and find IP addresses
    that are pingable on one subnet but not the other.

    This function validates the subnet and retries input,
    generates IP addresses for each subnet while excluding
    any IPs specified in the ignore list, and then pings
    both subnets. It returns a list of IP addresses that are
    pingable on one subnet but not the other.

    Args:
        subnet1 (str): The first subnet in
        CIDR format (e.g., "192.168.1.0/24").
        subnet2 (str): The second subnet in
        CIDR format (e.g., "192.168.2.0/24").
        retries (int, optional): The number of
        retries to attempt if a ping fails (default is 1).
        ignore_list (list, optional): A list of octets or
        IP addresses to exclude from the subnet (default is an empty list).

    Returns:
        list: A list of dictionaries where each dictionary
        contains pairs of IP addresses (one from each subnet).
              The dictionary indicates which IP is
              pingable on one subnet but not the other.
              For example: [{"192.168.1.1": True, "192.168.2.1": False}].

    Logs:
        - Warning: If the subnet inputs are invalid.
        - Warning: If pinging any of the IPs fails.

    Example:
        subnet1 = "192.168.1.0/24"
        subnet2 = "192.168.2.0/24"
        retries = 3
        ignore_list = ["192.168.1.5", "192.168.2.10"]
        unique_pingable = main(subnet1, subnet2, retries, ignore_list)
        print(unique_pingable)
        # Output: [{'192.168.1.1': True, '192.168.2.1': False},
        {'192.168.1.2': False, '192.168.2.2': True}]
    """
    logging.info("Initializing ping ...")
    # validate retries input
    retries = check_retries(retries=retries)

    # validate subnet input
    if not validate_subnet(subnet1) or not validate_subnet(subnet2):
        logging.warning("Invalid subnet inputs. Terminating ...")
        sys.exit(1)

    # Generate IP addresses for each subnet excluding ignored octets
    ips_subnet1 = validate_ignore_list(subnet=subnet1, ignore_list=ignore_list)
    ips_subnet2 = validate_ignore_list(subnet=subnet2, ignore_list=ignore_list)

    # Perform pinging
    results_subnet1, results_subnet2 = ping_both_subnets(
                ips_subnet1, ips_subnet2, retries)

    # find ip addresses that is pingable on one subnet but not the other
    unique_pingable = []
    for ip1, ip2 in zip(ips_subnet1, ips_subnet2):
        ping1 = results_subnet1[ip1]
        ping2 = results_subnet2[ip2]

        if ping1 and not ping2:
            unique_pingable.append({ip1: True, ip2: False})

        elif ping2 and not ping1:
            unique_pingable.append({ip1: False, ip2: True})
    logging.info("Pinging completed ...")

    return unique_pingable


if __name__ == "__main__":

    SUBNET_1 = '192.168.1.0/30'
    SUBNET_2 = '192.168.2.0/30'
    RETRIES = 2
    IGNORE_LIST = [25, 29]

    non_pingable_list = main(subnet1=SUBNET_1, subnet2=SUBNET_2,
                             retries=RETRIES, ignore_list=IGNORE_LIST)

    print(non_pingable_list)
