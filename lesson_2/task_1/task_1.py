"""
Создать функцию get_data(), в которой в цикле осуществляется перебор файлов с данными, их открытие и считывание данных.
В этой функции из считанных данных необходимо с помощью регулярных выражений извлечь значения параметров
«Изготовитель системы», «Название ОС», «Код продукта», «Тип системы».
Значения каждого параметра поместить в соответствующий список. Должно получиться четыре списка — например,
os_prod_list, os_name_list, os_code_list, os_type_list.
В этой же функции создать главный список для хранения данных отчета — например, main_data
— и поместить в него названия столбцов отчета в виде списка: «Изготовитель системы», «Название ОС»,
«Код продукта», «Тип системы». Значения для этих столбцов также оформить в виде списка и поместить
в файл main_data (также для каждого файла);
Создать функцию write_to_csv(), в которую передавать ссылку на CSV-файл.
В этой функции реализовать получение данных через вызов функции get_data(), а также сохранение подготовленных
данных в соответствующий CSV-файл;
Проверить работу программы через вызов функции write_to_csv().
"""

import re
import csv
import chardet


def get_data():
    headers = ['Изготовитель системы', 'Название ОС', 'Код продукта', 'Тип системы']
    os_prod_list = []
    os_name_list = []
    os_code_list = []
    os_type_list = []
    for i in range(1, 4):
        with open(f'info_{i}.txt', 'rb') as f:
            data_bytes = f.read()
            data_codepage = chardet.detect(data_bytes)
            data = data_bytes.decode(data_codepage['encoding'])

        pattern = re.compile(r'Изготовитель системы:.*')
        os_prod_list.append(pattern.findall(data)[0].split()[2])

        pattern = re.compile(r'Название ОС:.*')
        os_name_list.append(' '.join(pattern.findall(data)[0].split()[2:]))

        pattern = re.compile(r'Код продукта:.*')
        os_code_list.append(pattern.findall(data)[0].split()[2])

        pattern = re.compile(r'Тип системы:.*')
        os_type_list.append(pattern.findall(data)[0].split()[2])

    main_date = [headers]
    for line in zip(os_prod_list, os_name_list, os_code_list, os_type_list):
        main_date.append(line)

    return main_date


def write_to_csv(output_file):
    date = get_data()
    with open(output_file, 'w', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(date)


if __name__ == "__main__":
    write_to_csv('csv_date.csv')
