import re
import requests
import os
import urllib3
import chardet
import json
import concurrent.futures
from colorama import Fore, init
from sms import send_sms_requests  
from titlescreen import print_title_screen

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
init(autoreset=True)

current_version = '1.0.0'

def get_latest_version(url):
    try:
        response = requests.get(url)
        return response.text.strip()
    except Exception:
        return False

def is_valid_number(number, country_code):
    if country_code == "TR":
        pattern = r'^\d{10}$'
    else:
        pattern = r'^\d{7,11}$'
    return bool(re.match(pattern, number))

def validate_phone_numbers(phone_numbers, country_code):
    valid_numbers = []
    invalid_numbers = []

    for number in phone_numbers:
        if is_valid_number(number, country_code):
            valid_numbers.append(number)
        else:
            invalid_numbers.append(number)

    return valid_numbers, invalid_numbers

def get_country_code():
    while True:
        country_code = input(f"{Fore.MAGENTA}Enter target country code. Example 'US': {Fore.RESET}").strip().upper()
        try:
            with open('country_codes.json', 'r') as f:
                data = json.load(f)
                if country_code in data:
                    return country_code, data[country_code]
                else:
                    print(f"{Fore.RED}Country code not found. Please try again.{Fore.RESET}")
        except FileNotFoundError:
            print(f"{Fore.RED}country_codes.json not found. Quitting.{Fore.RESET}")
            exit(1)

def check_config_file(country_code):
    file_name = f"websiteconfigs/website_config_{country_code}.py"
    if os.path.isfile(file_name):
        return file_name
    else:
        print(f"{Fore.RED}Error: {file_name} not found. Quitting.{Fore.RESET}")
        return False

def get_phone_number_or_file(country_code, area_code):
    while True:
        choice = input(f"{Fore.MAGENTA}Enter (1) to input phone number or (2) to provide a file path: {Fore.RESET}").strip()
        if choice == '1':
            number = get_phone_number(country_code, area_code)
            return [number] if number else None, None
        elif choice == '2':
            return None, get_file_path()
        else:
            print(f"{Fore.RED}Invalid choice. Please enter '1' or '2'.{Fore.RESET}")

def get_phone_number(country_code, area_code):
    while True:
        number = input(f"{Fore.MAGENTA}Enter the target phone number (without +{area_code}) or press Enter to skip: {Fore.RESET}").strip()
        if not number:
            return None
        if is_valid_number(number, country_code):
            return number
        else:
            print(f"{Fore.RED}Invalid phone number format for {country_code}. Please try again.{Fore.RESET}")

def get_file_path(prompt=f"{Fore.MAGENTA}Enter the file path of the .txt file: {Fore.RESET}"):
    while True:
        file_path = input(prompt).strip()
        if os.path.isfile(file_path) and file_path.endswith('.txt'):
            return file_path
        else:
            print(f"{Fore.RED}Invalid file path or format. Please enter a valid .txt file.{Fore.RESET}")

def get_proxy_choice():
    while True:
        choice = input(f"{Fore.MAGENTA}Would you like to use a proxy? (y/n): {Fore.RESET}").strip().lower()
        if choice == 'y':
            return True
        elif choice == 'n':
            return False
        else:
            print(f"{Fore.RED}Invalid choice. Please enter 'y' or 'n'.{Fore.RESET}")

def is_valid_proxy(proxy):
    # Soporta: ip:port o ip:port:user:pass
    parts = proxy.split(':')
    if len(parts) not in (2, 4):
        return False
    ip_parts = parts[0].split('.')
    if len(ip_parts) != 4:
        return False
    try:
        port = int(parts[1])
        if not (1 <= port <= 65535):
            return False
        for octet in ip_parts:
            if not (0 <= int(octet) <= 255):
                return False
        return True
    except ValueError:
        return False

def validate_proxies(proxies):
    valid_proxies = []
    invalid_proxies = []
    for proxy in proxies:
        if is_valid_proxy(proxy):
            valid_proxies.append(proxy)
        else:
            invalid_proxies.append(proxy)
    return valid_proxies, invalid_proxies

def get_proxy_or_file():
    while True:
        choice = input(f"{Fore.MAGENTA}Enter (1) to input proxy details or (2) to provide a file path: {Fore.RESET}").strip()
        if choice == '1':
            proxy = input(f"{Fore.MAGENTA}Enter proxy (ip:port or ip:port:user:pass): {Fore.RESET}").strip()
            if is_valid_proxy(proxy):
                return [proxy]
            else:
                print(f"{Fore.RED}Invalid proxy format.{Fore.RESET}")
        elif choice == '2':
            file_path = get_file_path(f"{Fore.MAGENTA}Enter the file path of the .txt file containing proxies: {Fore.RESET}")
            try:
                proxies = read_file(file_path)
                if proxies:
                    return proxies
                else:
                    print(f"{Fore.RED}No valid proxies found in file.{Fore.RESET}")
            except Exception as e:
                print(f"{Fore.RED}Error reading proxy file: {e}{Fore.RESET}")
        else:
            print(f"{Fore.RED}Invalid choice. Please enter '1' or '2'.{Fore.RESET}")

def get_encoding(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']

def read_file(file_path):
    if not os.path.isfile(file_path):
        return []
    encoding = get_encoding(file_path)
    with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
        lines = [line.strip().split()[0] for line in f if line.strip()]
    return list(set(lines))  # Remove duplicates

def test_proxy(proxy, developer_mode=False):
    test_http_url = 'http://httpbin.org/ip'
    test_https_url = 'https://api.myip.com'
    proxy_results = {'http': False, 'https': False}

    try:
        parts = proxy.split(':')
        if len(parts) == 4:
            ip, port, user, pwd = parts
            proxy_url = f'http://{user}:{pwd}@{ip}:{port}'
        else:
            ip, port = parts
            proxy_url = f'http://{ip}:{port}'
        proxies = {'http': proxy_url, 'https': proxy_url}

        # Test HTTP
        resp_http = requests.get(test_http_url, proxies=proxies, timeout=10)
        proxy_results['http'] = resp_http.status_code == 200

        # Test HTTPS
        resp_https = requests.get(test_https_url, proxies=proxies, timeout=10)
        proxy_results['https'] = resp_https.status_code == 200

    except Exception as e:
        if developer_mode:
            print(f"{Fore.RED}Proxy test error for '{proxy}': {e}{Fore.RESET}")
    return proxy_results

def get_max_workers(proxies):
    return min(len(proxies), 50)

def test_proxies_and_show_results(proxies, developer_mode=False):
    http_proxies = []
    https_proxies = []

    print(f"{Fore.CYAN}Testing {len(proxies)} proxies...{Fore.RESET}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=get_max_workers(proxies)) as executor:
        future_to_proxy = {executor.submit(test_proxy, p, developer_mode): p for p in proxies}
        for future in concurrent.futures.as_completed(future_to_proxy):
            proxy = future_to_proxy[future]
            try:
                result = future.result()
            except Exception as e:
                continue

            parts = proxy.split(':')
            if len(parts) == 4:
                ip, port, user, pwd = parts
                http_url = f'http://{user}:{pwd}@{ip}:{port}'
                https_url = f'https://{user}:{pwd}@{ip}:{port}'
            else:
                ip, port = parts
                http_url = f'http://{ip}:{port}'
                https_url = f'https://{ip}:{port}'

            if result['http']:
                http_proxies.append(http_url)
            if result['https']:
                https_proxies.append(https_url)

            status = []
            if result['http']: status.append("HTTP")
            if result['https']: status.append("HTTPS")
            if status:
                print(f"{Fore.GREEN}{ip} {'/'.join(status)}{Fore.RESET}")
            else:
                print(f"{Fore.RED}{ip} FAILED{Fore.RESET}")

    print(f"{Fore.GREEN}Working HTTP proxies: {len(http_proxies)}")
    print(f"{Fore.GREEN}Working HTTPS proxies: {len(https_proxies)}")
    return http_proxies, https_proxies

def main():
    print_title_screen()
    print(r"""[ ! ] For authorized testing only. Use responsibly with explicit permission. Developer not responsible for illegal use.""")

    # Check version
    url = "https://raw.githubusercontent.com/farukalpay/SMS-Sender/main/version.txt"
    latest_version = get_latest_version(url)
    if latest_version and current_version != latest_version:
        print(Fore.RED + r"""[ ! ] You are using an outdated version. Update recommended:
https://github.com/farukalpay/SMS-Sender""")

    # Get country & config
    country_code, area_code = get_country_code()
    config_file = check_config_file(country_code)
    if not config_file:
        return

    # Get phone numbers
    phone_list, file_path = get_phone_number_or_file(country_code, area_code)
    if file_path:
        raw_numbers = read_file(file_path)
        if not raw_numbers:
            print(f"{Fore.RED}No numbers found in file. Quitting.{Fore.RESET}")
            return
        valid_nums, invalid_nums = validate_phone_numbers(raw_numbers, country_code)
        if invalid_nums:
            print(f"{Fore.YELLOW}Invalid numbers skipped: {len(invalid_nums)}")
        if not valid_nums:
            print(f"{Fore.RED}No valid phone numbers. Quitting.{Fore.RESET}")
            return
        phone_numbers = valid_nums
    elif phone_list:
        phone_numbers = phone_list
    else:
        print(f"{Fore.RED}No valid input provided. Quitting.{Fore.RESET}")
        return

    # Proxy setup
    http_proxies = []
    https_proxies = []
    if get_proxy_choice():
        raw_proxies = get_proxy_or_file()
        if not raw_proxies:
            print(f"{Fore.RED}No proxies provided. Quitting.{Fore.RESET}")
            return
        valid_proxies, invalid_proxies = validate_proxies(raw_proxies)
        if invalid_proxies:
            print(f"{Fore.YELLOW}Invalid proxies skipped: {len(invalid_proxies)}")
        if not valid_proxies:
            print(f"{Fore.RED}No valid proxies. Quitting.{Fore.RESET}")
            return
        http_proxies, https_proxies = test_proxies_and_show_results(valid_proxies)

    # Confirm send
    while True:
        choice = input(f"{Fore.MAGENTA}Start sending SMS? (y/n) or type 'developer' for debug mode: {Fore.RESET}").strip().lower()
        if choice == 'y':
            developer_mode = False
            break
        elif choice == 'developer':
            developer_mode = True
            break
        elif choice == 'n':
            print(f"{Fore.RED}SMS sending cancelled.{Fore.RESET}")
            return
        else:
            print(f"{Fore.RED}Please enter 'y', 'n', or 'developer'.{Fore.RESET}")

    # Final execution — ¡SOLO UNA VEZ!
    print_title_screen()
    print(f"{Fore.CYAN}Sending SMS to {len(phone_numbers)} number(s) using {len(http_proxies)+len(https_proxies)} proxy(es)...{Fore.RESET}")
    send_sms_requests(phone_numbers, http_proxies, https_proxies, config_file, developer_mode)

    print(f"\n{Fore.GREEN}✅ SMS sending process completed.{Fore.RESET}")

if __name__ == "__main__":
    main()