# Преобразовать слова «разработка», «администрирование», «protocol», «standard» из строкового представления
# в байтовое и выполнить обратное преобразование (используя методы encode и decode).
import chardet


def string_to_bytes(str):
    return str.encode('utf-8')


def bytes_to_string(str):
    return str.decode(chardet.detect(str)['encoding'])


strings = ['разработка', 'администрирование', 'protocol', 'standard']
strings_in_bytes = []

for string in strings:
    strings_in_bytes.append(string_to_bytes(string))

for string in strings_in_bytes:
    print(string)
    print(bytes_to_string(string))
