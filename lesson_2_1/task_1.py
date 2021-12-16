"""
Написать функцию host_ping(), в которой с помощью утилиты ping будет проверяться доступность сетевых узлов.
Аргументом функции является список, в котором каждый сетевой узел должен быть представлен именем хоста или ip-адресом.
В функции необходимо перебирать ip-адреса и проверять их доступность с выводом соответствующего сообщения
(«Узел доступен», «Узел недоступен»).
При этом ip-адрес сетевого узла должен создаваться с помощью функции ip_address().
"""
import ipaddress
import platform
from subprocess import Popen, PIPE, STDOUT


def ip_address(address):
    """
    Создает и возвращает объект IPv4Address  или IPv6Address если address ip адрес
    иначе возвращает address без изменений
    :param address:
    :return:
    """
    try:
        address = ipaddress.ip_address(address)
        return address
    except ValueError:
        return address


def host_ping(address_list):
    """
    Проверяет доступность узлов из списка address_list, возвращает список кортежей с адресом и результатом
    выполнения ping (0 - узел доступен, 1 - узел не доступен)
    :param address_list:
    :return:
    """
    PARAM = "-n" if platform.system().lower() == 'windows' else "-c"
    ping_result = []
    for address in address_list:
        address = ip_address(address)
        ARGS = ["ping", PARAM, "1", str(address)]
        process = Popen(ARGS, stdout=PIPE, stderr=STDOUT)
        code = process.wait()
        ping_result.append((address, code))
    return ping_result


def print_host_ping_result(ping_result):
    for res in ping_result:
        print(f'{res[0]} - {"Узел доступен" if res[1] == 0 else "Узел недоступен"}')


if __name__ == "__main__":
    result = host_ping(['google.com', 'yandex.ru', 'some_address', '195.211.205.214'])
    print_host_ping_result(result)
