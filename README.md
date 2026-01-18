# Лабораторная работа Архиватор на Python Леонов Даниил группа 932205

## Параметры: source Исходный файл или директория. dest Целевой файл или директория ключ -c для сжатия или ключ -ex для распаковки

## Ключ -h для справки, ключ -p для прогресс бара, ключ -b benchmark

## Примеры использования утилиты 
### Сжать файл:      python archive.py -c file.txt archive.zst -p
### Сжать папку:     python archive.py -c my_folder data.tar.bz2 -b -p
### Распаковать файл:  python archive.py -x archive.zst restored.txt
### Извлечь папку:   python archive.py -x data.tar.bz2 output_folder -b -p

## Тип алгоритма для архивации определяется по расширению у dest файла (.bz2 или .zstd) 

## Скриншот сжатия файла 
![1](screenshots\1.png)
## Скриншот распаковки файла
![2](screenshots\2.png)
## Скриншот сжатия папки
![3](screenshots\3.png)
## Скриншот распаковки папки
![4](screenshots\4.png)
