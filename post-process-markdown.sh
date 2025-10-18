#!/bin/sh

# 현재 디렉토리 및 하위 디렉토리에서 .md 파일을 찾아 처리합니다.
find . -type f -name "*.md" | while read -r file; do
  echo "Processing $file..."
  # macOS/BSD sed를 위한 스크립트
  # 1. ### Description, 빈 줄, N/A 패턴을 찾아 새 줄(\n) 하나로 치환합니다.
  # 2. 3줄 이상의 연속된 빈 줄을 하나의 빈 줄로 압축합니다.
  sed -i '' -e '/^### Description$/{N;N;s/### Description\n\nN\/A/\n/;}' \
             -e '/^$/{N;/^\n$/D;}' "$file"
done

echo "Done."
