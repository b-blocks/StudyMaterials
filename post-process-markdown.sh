#!/bin/sh

# 현재 디렉토리 및 하위 디렉토리에서 .md 파일을 찾아 처리합니다.
find . -type f -name "*.md" | while read -r file; do
  echo "Processing $file..."
  # macOS와 BSD sed를 위한 -i '' 옵션. GNU sed에서는 -i만 사용합니다.
  # ### Description, 빈 줄, N/A 패턴을 찾아서 삭제.
  # -E 옵션은 확장 정규 표현식을 사용하기 위함입니다.
  sed -i '' -E '/^### Description$/{N;N;s/### Description\n\nN\/A//g;}' "$file"
done

echo "Done."
