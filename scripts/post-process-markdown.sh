#!/bin/bash

##########################
# Markdown 후처리 스크립트 
##########################
find ../ -type f -name "*.md" | while read -r file; do
  echo "Processing $file..."
  # macOS/BSD sed를 위한 스크립트. 다음 세 가지 작업을 순차적으로 수행합니다.
  # 1. "YouTube 영상 학습 자료: " 라는 줄을 삭제합니다.
  # 2. Description, 빈 줄, N/A 패턴을 찾아 새 줄(\n) 하나로 치환합니다.
  # 3. 3줄 이상의 연속된 빈 줄을 하나의 빈 줄로 압축합니다.
  sed -i '' -e '/YouTube 영상 학습 자료: /d' \
             -e '/^### Description$/{N;N;s/### Description\n\nN\/A/\n/;}' \
             -e '/^$/{N;/^\n$/D;}' "$file"
done

echo "Done."
