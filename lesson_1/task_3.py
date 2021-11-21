# Определить, какие из слов «attribute», «кслас», «функция», «type» невозможно записать в байтовом типе.
# bytes can only contain ASCII literal characters

def check_string(str):
    for ch in str:
        if ord(ch) > 127:
            return f'строку {str} НЕЛЬЗЯ представить в байтовом типе'
    return f'строку {str} МОЖНО представить в байтовом типе'


if __name__ == "__main__":
    strings = ['attribute', 'кслас', 'функция', 'type']
    for string in strings:
        print(check_string(string))
