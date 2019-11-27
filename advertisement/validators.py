import six
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

PERSIAN_TEXT_MAPPING = {
    '۰': '0',
    '۱': '1',
    '۲': '2',
    '۳': '3',
    '۴': '4',
    '۵': '5',
    '۶': '6',
    '۷': '7',
    '۸': '8',
    '۹': '9',
}

def normalize_persian_characters(text):
    normalized_text = ''
    for pos in range(len(text)):
        normalized_text += PERSIAN_TEXT_MAPPING.get(text[pos], text[pos])
    return normalized_text

def phone_validator(phone):
    if not string_check(phone, min_length=11, max_length=11)[0]:
        return False, 'Not a valid Iran mobile number'
    phone = normalize_persian_characters(phone).strip()
    if not phone.startswith('09'):
        return False, 'Not a valid Iran mobile number'
    return True, phone

def string_check(text, verbose_name='ورودی', min_length=None, max_length=None, alphanumeric=False):
    if not isinstance(text, six.string_types):
        return False, 'Invalid string'
    text = text.strip()
    if min_length and len(text) < min_length:
        return False, '{} نباید کمتر از {} کاراکتر باشد'.format(verbose_name, min_length)
    if max_length and len(text) > max_length:
        return False, '{} نباید بیشتر از {} کاراکتر باشد'.format(verbose_name, max_length)
    if alphanumeric and not text.isalnum():
        return False, '{} تنها می‌تواند شامل اعداد و حروف بزرگ و کوچک انگلیسی باشد'.format(verbose_name)
    return True, text