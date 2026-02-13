import requests
import random
import string
import time
import itertools
import json
import urllib3
import importlib.util
from colorama import Fore, init

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

init(autoreset=True)

def random_turkish_name_surname_gmail():
    first_names = [
        'Benedict', 'Clarence', 'Dominic', 'Ferdinand', 'Gulliver', 'Humphrey', 'Ignatius', 'Jebediah', 'Leopold', 
        'Mordecai', 'Nathanael', 'Octavius', 'Percival', 'Quintus', 'Rafferty', 'Sylvester', 'Thaddeus', 'Ulysses', 
        'Vincenzo', 'Wilfred', 'Xavier', 'Yannick', 'Zacharia', 'Algernon', 'Bertrand', 'Cuthbert', 'Demetrius', 'Ebenezer',
        'Fitzwilliam', 'Giovanni', 'Hercules', 'Isidore', 'Jeremiah', 'Kermit', 'Lazarus', 'Marcellus', 'Nehemiah', 'Obadiah', 
        'Ptolemy', 'Quentin', 'Roderick', 'Sebastian', 'Theophilus', 'Umberto', 'Valentine', 'Wolfgang', 'Xerxes', 'Yehudi', 'Zebedee'
    ]

    last_names = [
        'Blackwood', 'Carmichael', 'Davenport', 'Eggleston', 'Fitzgerald', 'Greenwood', 'Hemingway', 'Iverson', 'Jefferies', 
        'Kilgore', 'Livingston', 'Macdonald', 'Nightingale', 'Sullivan', 'Pendleton', 'Quigley', 'Rothschild', 'Sutherland', 
        'Tennyson', 'Underwood', 'Van Dyke', 'Whittington', 'Xanthopoulos', 'Yardley', 'Zimmermann', 'Abernathy', 'Buckminster', 
        'Cobblepot', 'Dumbledore', 'Fitzroy', 'Goldsmith', 'Hawthorne', 'Inglewood', 'Jekyll', 'Kingsley', 'Lancaster', 'Macmillan', 
        'Nickleby', 'Oglethorpe', 'Pilkington', 'Quincy', 'Ravenclaw', 'Stratford', 'Thornberry', 'Underhill', 'Vanderbilt', 'Worthington',
        'Xavier', 'Yellowknife', 'Zephaniah'
    ]

    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    def _random_string(length):
        return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))
    username = f"{first_name.lower()}{last_name.lower()}{_random_string(4)}"
    return first_name, last_name, f"{username}@gmail.com"

def import_from_filepath(filepath):
    spec = importlib.util.spec_from_file_location("module.name", filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def shuffle_proxies(proxies):
    random.shuffle(proxies)
    return proxies

def get_next_proxy(proxy_iterator_container, proxies):
    try:
        return next(proxy_iterator_container[0])
    except StopIteration:
        shuffled_proxies = shuffle_proxies(proxies)
        proxy_iterator_container[0] = itertools.cycle(shuffled_proxies)
        return next(proxy_iterator_container[0])

def decompose_proxy_url(proxy_url, key):
    proxy_parts = {}
    if '@' in proxy_url:
        user_pass, ip_port = proxy_url.split('@')
        username, password = user_pass.split('//')[1].split(':')
        proxy_parts['username'] = username
        proxy_parts['password'] = password
    else:
        ip_port = proxy_url.split('//')[1]
    ip, port = ip_port.split(':')
    proxy_parts['ip'] = ip
    proxy_parts['port'] = port
    return proxy_parts.get(key)

def handle_response(response, success_criteria, failure_msg, response_base, developer_mode=False, proxy=False):
    if developer_mode:
        print(f"Response: {response.text}")
        print(f"Response status code: {response.status_code}")
        print(f"Proxy: {proxy}")
        
    # success_criteria and failure_msg could be a list or a string, ensure they are always lists of strings for consistency
    success_criteria = [str(criteria) for criteria in (success_criteria if isinstance(success_criteria, list) else [success_criteria])]
    if failure_msg:
        failure_msg = [str(msg) for msg in (failure_msg if isinstance(failure_msg, list) else [failure_msg])]
    if response_base == "text":
        check_attribute = response.text
        if any(criteria in check_attribute for criteria in success_criteria):
            return (True, True, 'successful') if proxy else (True, 'successful')
        elif any(msg in check_attribute for msg in failure_msg):
            return (False, True, 'failure') if proxy else (False, 'failure')
    elif response_base == "status":
        status_code = str(response.status_code)
        if status_code in success_criteria:
            return (True, True, 'successful') if proxy else (True, 'successful')
        else:
            return (False, True, 'failure') if proxy else (False, 'failure')
    return (False, True, 'unknown response') if proxy else (False, 'unknown response')
        
def handle_errors(developer_mode, e=None, proxy=None):
    if isinstance(e, requests.exceptions.Timeout):
        return (False, False, 'response timeout') if proxy else (False, 'response timeout')
    else:
        if developer_mode and e:
            print(f"Error: {str(e)}")
        return (False, False, 'exception') if proxy else (False, 'exception')

def send_request(session, phone_number, first_name, last_name, gmail, config, developer_mode=False, proxy=False):
    
    try:
        url = config['url']
        method = config.get('method', 'POST')  # Default to 'POST' if not specified

        payload_function = config['payload_function']
        payload = payload_function(first_name, last_name, gmail, phone_number)

        if config.get('send_as_json', False):
            payload = json.dumps(payload)  # Convert the payload to a JSON string if send_as_json is True

        headers = {}
        if config.get('send_with_headers', False):
            headers = config.get('headers', {})  # Get headers from config if send_with_headers is True
            if config.get('send_as_json', False):
                headers['Content-Type'] = 'application/json'  # Ensure the content type is set to JSON
        else:
            headers = None
        if config.get('send_with_cookies', False):
            cookies = config.get('cookies', {})
        else:
            cookies = None
        if config.get('response_base') in ["text", "status"]:
            response_base = config.get('response_base', {})
        else:
            print(f"{Fore.RED}response_base is not valid. Quiting..")
            return
        if proxy != "null":
            try:
                proxies = {'http': proxy,
                           'https': proxy
                        }
                if method.upper() == 'POST':
                    if headers and developer_mode:
                        print(headers) 
                    response = session.post(url, proxies=proxies, headers=headers if headers else None, cookies=cookies if cookies else None, data=payload, timeout=50, verify=False)
                elif method.upper() == 'GET':
                    response = session.get(url, proxies=proxies, headers=headers if headers else None, cookies=cookies if cookies else None, params=payload, timeout=50, verify=False)
                return handle_response(
                    response,
                    config['success'] if response_base == "text" else config['status_code'],
                    config['failure'] if response_base == "text" else False,
                    response_base,
                    developer_mode,
                    proxy
                )
            except Exception as e:
                return handle_errors(developer_mode, e, proxy)
        else:
            if method.upper() == 'POST':
                try:
                    if headers and developer_mode:
                        print(headers)
                    response = session.post(url, headers=headers if headers else None, cookies=cookies if cookies else None, data=payload, timeout=50, verify=False)
                except Exception as e:
                    return handle_errors(developer_mode, e)
            elif method.upper() == 'GET':
                try:
                    response = session.get(url, headers=headers if headers else None, cookies=cookies if cookies else None, params=payload, timeout=50, verify=False)
                except Exception as e:
                    return handle_errors(developer_mode, e)
            return handle_response(
                response,
                config['success'] if response_base == "text" else config['status_code'],
                config['failure'] if response_base == "text" else False,
                response_base,
                developer_mode,
                False
            )
    except Exception as e:
        if developer_mode:
            print(f"Error: {str(e)}")
        return False, False, 'exception'

def send_single_sms_requests(phone_numbers, http_proxies, https_proxies, filepath, developer_mode=False):
    website_configs = import_from_filepath(filepath).website_configs
    total_successful_requests = 0
    total_failed_requests = 0
    total_unknown_requests = 0
    successful_requests = {pn: 0 for pn in phone_numbers}
    failed_requests = {pn: 0 for pn in phone_numbers}
    unknown_requests = {pn: 0 for pn in phone_numbers}

    proxies = bool(http_proxies or https_proxies)
    proxy_methods = {}
    if proxies:
        http_proxies = shuffle_proxies(http_proxies)
        https_proxies = shuffle_proxies(https_proxies)
        proxy_methods = {
            "http": (itertools.cycle(http_proxies), http_proxies),
            "https": (itertools.cycle(https_proxies), https_proxies),
        }

    session = requests.Session()

    for index, phone_number in enumerate(phone_numbers, start=1):
        first_name, last_name, gmail = random_turkish_name_surname_gmail()

        for website, config in website_configs.items():
            url = config['url']
            protocol = url.split('://', 1)[0]
            if protocol not in ["http", "https"]:
                print(f'{Fore.RED}Error: protocol must be "http" or "https". Found: {protocol}')
                continue

            proxy_used = None
            result = None

            if proxies and protocol in proxy_methods and proxy_methods[protocol][1]:
                proxy_iter, proxy_list = proxy_methods[protocol]
                max_attempts = min(3, len(proxy_list))  # Intentar con hasta 3 proxies distintos
                for _ in range(max_attempts):
                    proxy_used = next(proxy_iter)
                    result = send_request(session, phone_number, first_name, last_name, gmail, config, developer_mode, proxy_used)
                    success, success_req, msg = result if proxies else (*result, None)
                    if success_req:
                        break
                    if developer_mode:
                        print(f"{Fore.RED}Proxy {proxy_used} falló. Reintentando...")
                else:
                    print(f"{Fore.RED}Todos los intentos con proxies fallaron para {website}.")
                    continue
            else:
                result = send_request(session, phone_number, first_name, last_name, gmail, config, developer_mode, False)
                success, msg = result
                success_req = success  # Para uniformidad

            # Registro del resultado
            if success_req:
                successful_requests[phone_number] += 1
                total_successful_requests += 1
                proxy_display = decompose_proxy_url(proxy_used, 'ip') if proxy_used else "direct"
                print(f"{Fore.CYAN}[{website}]{Fore.GREEN} Éxito para {phone_number} (#{index}) usando proxy {proxy_display}.")
            else:
                if msg == 'unknown response':
                    unknown_requests[phone_number] += 1
                    total_unknown_requests += 1
                    print(f"{Fore.CYAN}[{website}]{Fore.YELLOW} Respuesta desconocida para {phone_number}.")
                else:
                    failed_requests[phone_number] += 1
                    total_failed_requests += 1
                    print(f"{Fore.CYAN}[{website}]{Fore.RED} Falló para {phone_number}.")

    # Resumen final
    print(f"\n{Fore.BLUE}=== RESUMEN ===")
    print(f"{Fore.GREEN}Éxitos totales: {total_successful_requests}")
    print(f"{Fore.RED}Fallos totales: {total_failed_requests}")
    print(f"{Fore.YELLOW}Respuestas desconocidas: {total_unknown_requests}")
    for pn in phone_numbers:
        print(f"{pn}: ✅ {successful_requests[pn]} | ❌ {failed_requests[pn]} | ? {unknown_requests[pn]}")

