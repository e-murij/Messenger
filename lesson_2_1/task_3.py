"""
Написать функцию host_range_ping_tab(),
возможности которой основаны на функции из примера 2.
Но в данном случае результат должен быть итоговым по всем ip-адресам,
представленным в табличном формате (использовать модуль tabulate).
"""
from tabulate import tabulate
from task_1 import host_ping
from task_2 import host_range_ping


def host_range_ping_tab(ping_result):
    """
    Получает список кортежей с адресом и результатом выполнения ping (0 - узел доступен, 1 - узел не доступен)
    Выводит таблицу с адресами, разделенными на колонки 'Reachable' и 'Unreachable'
    :param ping_result:
    :return:
    """
    reachable_ip = []
    unreachable_ip = []
    for res in ping_result:
        if res[1] == 0:
            reachable_ip.append(res[0])
        else:
            unreachable_ip.append(res[0])
    table = {'Reachable': reachable_ip, 'Unreachable': unreachable_ip}
    print(tabulate(table, headers="keys"))


if __name__ == '__main__':
    address_list = host_range_ping()
    result = host_ping(address_list)
    host_range_ping_tab(result)
