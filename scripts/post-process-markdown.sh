#!/bin/bash

##########################
# Markdown 후처리 스크립트 
##########################
find ../ -type f -name "*.md" | while read -r file; do
  echo "Processing $file..."
  # 1. "### ### "로 시작하는 줄을 "### "로 변경
  sed -i '' 's/^### ### /### /g' "$file"
  sed -i '' 's/^#### ### /#### /g' "$file"
  sed -i '' 's/^#### #### /#### /g' "$file"
  sed -i '' 's/^##### ### /##### /g' "$file"
  
  # 2. 3줄 이상의 연속된 빈 줄을 하나의 빈 줄로 압축
  sed -i '' '/^$/N;/^\n$/N;/^\n\n$/d' "$file"
done
echo "Done."
