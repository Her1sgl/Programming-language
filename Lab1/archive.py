import argparse
import bz2
from compression import zstd
import os
import sys
import tarfile
import time
from pathlib import Path

def get_size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    elif path.is_dir():
        return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
    return 0

def show_progress(processed_bytes: int, total_bytes: int, label: str = ""):
    if total_bytes == 0:
        return
    bar_length = 30
    percent = processed_bytes / total_bytes
    filled_length = int(bar_length * percent)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    sys.stdout.write(f'\r{label} |{bar}| {percent*100:5.1f}%')
    sys.stdout.flush()
    if processed_bytes >= total_bytes:
        print()


def make_tar(source_dir: Path, tar_path: Path):
    with tarfile.open(tar_path, "w") as tf:
        tf.add(source_dir, arcname=source_dir.name)

def extract_tar(tar_path: Path, dest_dir: Path):
    dest_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tar_path, "r") as tf:
        tf.extractall(path=dest_dir)

def compress_stream(source_path: Path, dest_path: Path, progress: bool):
    open_func = None
    if dest_path.suffix == '.zstd':
        open_func = zstd.open
    elif dest_path.suffix == '.bz2':
        open_func = bz2.open
    else:
        raise ValueError(f"Неподдерживаемое расширение: {dest_path.suffix}")

    total_size = get_size(source_path)
    processed_size = 0
    
    with open(source_path, 'rb') as f_in, open_func(dest_path, 'wb') as f_out:
        chunk_size = 1024 * 1024 
        while True:
            chunk = f_in.read(chunk_size)
            if not chunk:
                break
            f_out.write(chunk)
            if progress:
                processed_size += len(chunk)
                show_progress(processed_size, total_size)

def decompress_stream(source_path: Path, dest_path: Path, progress: bool):
    decompressor = None
    if source_path.suffix == '.zstd':
        decompressor = zstd.ZstdDecompressor()
    elif source_path.suffix == '.bz2':
        decompressor = bz2.BZ2Decompressor()
    else:
        raise ValueError(f"Неподдерживаемый формат: {source_path.suffix}")
    
    total_size = get_size(source_path)
    processed_size = 0
    
    try:
        with open(source_path, 'rb') as f_in, open(dest_path, 'wb') as f_out:
            while chunk := f_in.read(1024 * 1024):
                processed_size += len(chunk)
                decompressed_chunk = decompressor.decompress(chunk)
                f_out.write(decompressed_chunk)
                if progress:
                    show_progress(processed_size, total_size)

    except Exception as e:
        print(f"\nОшибка при распаковке файла: {e}", file=sys.stderr)
        if dest_path.exists():
            dest_path.unlink()
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Архиватор/разархиватор zstd/bz2",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-c", "--compress", action="store_true", help="Режим сжатия.")
    group.add_argument("-ex", "--extract", action="store_true", help="Режим распаковки.")
    
    parser.add_argument("source", type=Path, help="Исходный файл или директория.")
    parser.add_argument("dest", type=Path, help="Целевой файл или директория.")
    parser.add_argument("-b", "--benchmark", action="store_true", help="Показать время и статистику по размерам.")
    parser.add_argument("-p", "--progress", action="store_true", help="Показать прогресс-бар.")
    
    args = parser.parse_args()

    start_time = time.perf_counter()

    if args.compress:
        if args.source.is_dir():
            temp_tar_path = args.dest.with_suffix('.tmp.tar')
            try:
                make_tar(args.source, temp_tar_path)
                compress_stream(temp_tar_path, args.dest, args.progress)
            finally:
                if temp_tar_path.exists():
                    temp_tar_path.unlink()
        else:
            compress_stream(args.source, args.dest, args.progress)

    else:
        if args.source.name.endswith(('.tar.zstd', '.tar.bz2')):
            args.dest.mkdir(parents=True, exist_ok=True)
            temp_tar_path = args.dest / (args.source.stem + '.tmp.tar')
            try:
                decompress_stream(args.source, temp_tar_path, args.progress)
                extract_tar(temp_tar_path, args.dest)
            finally:
                if temp_tar_path.exists():
                    temp_tar_path.unlink()
        else:
            if args.dest.is_dir():
                args.dest.mkdir(parents=True, exist_ok=True)
                final_dest = args.dest / args.source.stem
            else:
                final_dest = args.dest
            decompress_stream(args.source, final_dest, args.progress)

    print("\nОперация успешно завершена.")
    
    if args.benchmark:
        elapsed = time.perf_counter() - start_time
        input_sz = get_size(args.source)
        output_sz = get_size(args.dest) if args.dest.exists() else 0
        
        print("\n" + "="*50)
        print("РЕЗУЛЬТАТЫ БЕНЧМАРКА")
        print(f"Время выполнения: {elapsed:.3f} сек")
        print(f"Размер источника: {input_sz / 1024:.2f} КБ")
        print(f"Размер результата: {output_sz / 1024:.2f} КБ")
        if args.compress and input_sz > 0:
            ratio = output_sz / input_sz
            print(f"Коэффициент сжатия: {ratio:.2f}")
        print("="*50)

if __name__ == "__main__":
    main()