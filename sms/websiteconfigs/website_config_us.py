website_configs = {
    'website1': {
        'url': 'http://www.website1.com/registration/',
        'method': 'POST',
        'send_as_json': False,
        'payload_function': lambda first_name, last_name, gmail, phone_number: {
            'first_name': first_name,
            'last_name': last_name,
            'email': gmail,
            'password': 'cactusboy1234',
            'confirm': 'true',
            'phone': phone_number
        },
        'send_with_headers': True,
        'headers': {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        'send_with_cookies': False,
        'cookies': {},
        'response_base': 'status',
        'status_code': ['200', '201', '202', '203', '204'],
        # 'success' y 'failure' se ignoran en modo 'status' → opcional eliminarlos
    },
    'website2': {
        'url': 'http://www.website2.com/registration/',
        'method': 'GET',
        'send_as_json': True,
        'payload_function': lambda first_name, last_name, gmail, phone_number: {
            'phonenumber': f'0{phone_number}'
        },
        'send_with_headers': False,
        'headers': {},
        'send_with_cookies': False,
        'cookies': {},
        'response_base': 'text',
        'success': 'registered',      # usado en modo 'text'
        'failure': ['0', '1', 'true'], # usado en modo 'text'
    },
}