#!/bin/bash

##########################
# Markdown 후처리 스크립트 
##########################
# find ../ -type f -name "*.md" | while read -r file; do
#   echo "Processing $file..."
#   
#   # 모든 sed 명령을 하나로 통합
#   sed -i '' \
#     -e 's/^### ## /### /g' \
#     -e 's/^### ### /### /g' \
#     -e 's/^#### ### /#### /g' \
#     -e 's/^#### #### /#### /g' \
#     -e 's/^##### ### /##### /g' \
#     -e 's/핵심 요약 (Executive Summary)/핵심 요약/g' \
#     -e 's/핵심 요약 (Hook)/핵심 요약/g' \
#     -e 's/상세 내용 (Detailed Content)/상세 내용/g' \
#     -e 's/상세 내용 (Storyline)/상세 내용/g' \
#     -e 's/참고 자료 (References & Further Reading)/참고 자료/g' \
#     -e '/^$/N;/^\n$/N;/^\n\n$/d' \
#     "$file"
# done
# echo "Done."

find ../ -type f -name "*.md" | while read -r file; do
  echo "Processing $file..."
  # 1. "### ### "로 시작하는 줄을 "### "로 변경
  sed -i '' 's/^### ## /### /g' "$file"
  sed -i '' 's/^### ### /### /g' "$file"
  sed -i '' 's/^#### ### /#### /g' "$file"
  sed -i '' 's/^#### #### /#### /g' "$file"
  sed -i '' 's/^##### ### /##### /g' "$file"
  sed -i '' 's/핵심 요약 (Executive Summary)/핵심 요약/g' "$file"
  sed -i '' 's/핵심 요약 (Hook)/핵심 요약/g' "$file"
  sed -i '' 's/상세 내용 (Detailed Content)/상세 내용/g' "$file"
  sed -i '' 's/상세 내용 (Storyline)/상세 내용/g' "$file"
  sed -i '' 's/참고 자료 (References & Further Reading)/참고 자료/g' "$file"
  sed -i '' 's/상세 내용 (Storyline)/상세 내용/g' "$file"
  sed -i '' 's/YouTube 영상.*자료: //g' "$file"
  sed -i '' 's/다음은 YouTube 영상의 자막 내용을.*학습 자료입니다.//g' "$file"
  # 2. 3줄 이상의 연속된 빈 줄을 하나의 빈 줄로 압축
  sed -i '' '/^$/N;/^\n$/N;/^\n\n$/d' "$file"
done
echo "Done."