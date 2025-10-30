#!/usr/bin/python3
import sys
import os

def main(args):
    if len(args) < 2:
        print(f"Usage: python {args[0]} <markdown_file>")
        return

    markdown_file = args[1]
    base_name = markdown_file[:-3] #.md 확장자 제거
    
    # 출력 디렉토리 생성
    output_dir = f"{base_name}"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    file_idx = 1
    lines_buffer = []
    MAX_LINES = 3800

    with open(markdown_file, 'r') as f:
        for line in f:
            if len(lines_buffer) >= MAX_LINES and line.startswith('## '):
                output_file_name = os.path.join(output_dir, f"{os.path.basename(base_name)}-{file_idx:03}.md")
                with open(output_file_name, 'w') as out_f:
                    out_f.writelines(lines_buffer)
                print(f"Created {output_file_name}")
                lines_buffer = []
                file_idx += 1
            lines_buffer.append(line)

    # 마지막 남은 내용을 파일로 저장
    if lines_buffer:
        output_file_name = os.path.join(output_dir, f"{os.path.basename(base_name)}-{file_idx:03}.md")
        with open(output_file_name, 'w') as out_f:
            out_f.writelines(lines_buffer)
        print(f"Created {output_file_name}")


if __name__ == "__main__":
    main(sys.argv)
