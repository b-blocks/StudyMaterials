#!/bin/bash

# 사용법을 안내하는 함수
usage() {
  echo "Usage: $0 <filename.md>"
  echo "Example: $0 aaa.md"
  exit 1
}

# 파일 이름이 인자로 전달되었는지 확인
if [ -z "$1" ]; then
  echo "오류: 파일 이름을 입력해주세요."
  usage
fi

INPUT_FILE="$1"

# 입력된 파일이 실제로 존재하는지 확인
if [ ! -f "$INPUT_FILE" ]; then
  echo "오류: '$INPUT_FILE' 파일을 찾을 수 없습니다."
  exit 1
fi

# 파일 확장자를 제외한 기본 이름을 추출 (예: aaa.md -> aaa)
PREFIX=$(basename "$INPUT_FILE" .md)

echo "파일 분할을 시작합니다: '$INPUT_FILE'"
echo "결과 파일 접두사: '${PREFIX}-'"

# 파일을 4000줄 단위로 분할합니다.
# -l 4000: 4000줄 단위
# -d: 숫자 접미사 사용 (0, 1, 2...)
# -a 1: 접미사 길이를 1로 설정
split -l 4000 -d -a 1 "$INPUT_FILE" "${PREFIX}-"

# split 명령어 실행 성공 여부 확인
if [ $? -ne 0 ]; then
    echo "오류: 파일 분할에 실패했습니다."
    exit 1
fi

echo "파일 분할 완료. 확장자를 변경합니다..."

# 분할된 파일들에 .md 확장자를 추가
for file in "${PREFIX}-"*; do
  # 파일이 실제로 존재하는지 확인 (분할된 파일이 없을 경우 대비)
  if [ -f "$file" ]; then
    mv "$file" "$file.md"
    echo "  - '$file' -> '$file.md'"
  fi
done

echo "모든 작업이 완료되었습니다."

