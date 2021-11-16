# Каждое из слов «class», «function», «method» записать в байтовом типе без преобразования впоследовательность кодов
# (не используя методы encode и decode) и определить тип, содержимое и длину соответствующих переменных.
if __name__ == "__main__":
    strings = ['class', 'function', 'method']
    for string in strings:
        str_bytes = eval(f'b"{string}"')
        print(type(str_bytes), str_bytes, len(str_bytes))
