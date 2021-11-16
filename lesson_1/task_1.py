# Каждое из слов «разработка», «сокет», «декоратор» представить в строковом формате и проверить тип
# и содержание соответствующих переменных. Затем с помощью онлайн-конвертера преобразовать
# строковые представление в формат Unicode и также проверить тип и содержимое переменных.

def print_type_strings(str_list):
    for string in str_list:
        print(type(string), string)


if __name__ == "__main__":
    strings = ['разработка', 'сокет', 'декоратор']
    strings_unicode = [
        '\u0440\u0430\u0437\u0440\u0430\u0431\u043e\u0442\u043a\u0430',
        '\u0441\u043e\u043a\u0435\u0442',
        '\u0434\u0435\u043a\u043e\u0440\u0430\u0442\u043e\u0440'
    ]
    print('string:')
    print_type_strings(strings)
    print('string unicode:')
    print_type_strings(strings_unicode)
