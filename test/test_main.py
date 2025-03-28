import pytest
import ipaddress
from ping_subnets.main import check_retries, validate_subnet
from ping_subnets.main import validate_ignore_list, ping_subnet

def test_valid_check_retries():
    '''
    tests a valid retries input
    '''
    retries = 2
    result = check_retries(retries)
    assert result == 2

def test_invalid_check_retries():
    '''
    tests an invalid retries
    '''
    retries = 4
    result = check_retries(retries)
    assert result == 1

def test_validate_subnet_1():
    '''
    tests a valid subnet input with CIDR notation
    '''
    subnet = "192.168.1.0/24"
    result = validate_subnet(subnet)

    assert result == True

def test_validate_subnet_2():
    '''
    tests a valid subnet input without CIDR notation
    '''
    subnet = "192.168.1.0"
    result = validate_subnet(subnet)

    assert result == False

def test_validate_subnet_3():
    '''
    tests an invalid subnet input without CIDR notation
    '''
    subnet = "255.255.255.0"
    result = validate_subnet(subnet)

    assert result == False

def test_validate_subnet_4():
    '''
    tests an invalid subnet input with CIDR notation
    '''
    subnet = "192.168.1.64/24"
    result = validate_subnet(subnet)

    assert result == False

def test_validate_subnet_5():
    '''
    tests an invalid subnet input with CIDR notation
    and hosts bit set
    '''
    subnet = "192.168.1.1/24"
    result = validate_subnet(subnet)

    assert result == False

def test_validate_subnet_6():
    '''
    tests a valid subnet input with non /24
    CIDR notation
    '''
    subnet = "192.168.1.0/30"
    result = validate_subnet(subnet)

    assert result == False

def test_ignore_list_1():
    '''
    tests a valid ignore_list
    '''
    subnet = "192.168.1.0/24"
    ignore_list = [25, 27]
    network = ipaddress.IPv4Network(subnet, strict=True)
    
    result = validate_ignore_list(subnet, ignore_list)
    expected_list = [str(ip) for ip in list(network.hosts())
                     if ip.packed[-1] not in ignore_list]
    assert result == expected_list


def test_ignore_list_2():
    '''
    test whether ignore list excludes
    an invalid octet value (i.e. 280)
    '''
    subnet = "192.168.1.0/24"
    ignore_list = [25, 280]
    network = ipaddress.IPv4Network(subnet, strict=True)
    
    result = validate_ignore_list(subnet, ignore_list)
    expected_list = [str(ip) for ip in list(network.hosts())
                     if ip.packed[-1] not in ignore_list]

    assert result == expected_list
