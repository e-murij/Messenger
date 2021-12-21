"""
2. Написать функцию host_range_ping() для перебора ip-адресов из заданного диапазона.
Меняться должен только последний октет каждого адреса. По результатам проверки
должно выводиться соответствующее сообщение.
"""
import ipaddress
from pprint import pprint

from task_1 import host_ping, print_host_ping_result


def host_range_ping():
    """
    Запрашивает начальный ip адрес и количество адресов, которые необходимо получить
    возвращает список ip адресов
    Меняется только последний октет каждого адреса
    :return:
    """
    result_ip_list = []
    try:
        start_ip = input('Введите начальный ip-адрес: ')
        start_ip = ipaddress.ip_address(start_ip)
        range_ip = int(input('Введите необходимое количество адресов: '))
    except ValueError:
        print('Неверно введен ip адрес или количество адресов')
        return result_ip_list
    for i in range(range_ip):
        if int(str(start_ip).split('.')[-1]) + i < 256:
            result_ip_list.append(start_ip + i)
        elif int(str(start_ip).split('.')[-1]) - i > 0:
            result_ip_list.append(start_ip - (range_ip - i))
        else:
            return result_ip_list
    return result_ip_list


if __name__ == '__main__':
    address_list = host_range_ping()
    print_host_ping_result(host_ping(address_list))
