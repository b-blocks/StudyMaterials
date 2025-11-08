# -*- coding: utf-8 -*-
import re
import os
import glob


import re
from collections import defaultdict
from typing import List, Tuple, Set

class TextDeduplicator:
    """연속 반복되는 단어/문장 패턴을 제거하는 클래스"""
    
    def __init__(self, min_repeat: int = 3, max_ngram: int = 20):
        """
        Args:
            min_repeat: 최소 반복 횟수 (기본: 3회)
            max_ngram: 검사할 최대 n-gram 크기 (기본: 20단어)
        """
        self.min_repeat = min_repeat
        self.max_ngram = max_ngram
    
    def tokenize(self, text: str) -> List[str]:
        """텍스트를 단어 단위로 토큰화"""
        # 공백 기준으로 분리하되, 구두점도 보존
        tokens = text.split()
        return tokens
    
    def find_consecutive_repeats(self, words: List[str]) -> Set[Tuple[int, int]]:
        """연속 반복되는 패턴의 위치를 찾음
        
        Returns:
            제거할 영역의 (start, end) 인덱스 집합
        """
        to_remove = set()
        removed_mask = [False] * len(words)
        
        # 긴 패턴부터 검사 (더 구체적인 패턴 우선)
        for ngram_size in range(min(self.max_ngram, len(words) // self.min_repeat), 0, -1):
            i = 0
            while i <= len(words) - ngram_size:
                # 이미 제거된 영역은 스킵
                if removed_mask[i]:
                    i += 1
                    continue
                
                # 현재 n-gram
                pattern = tuple(words[i:i + ngram_size])
                
                # 연속으로 몇 번 반복되는지 체크
                repeat_count = 1
                j = i + ngram_size
                
                while j + ngram_size <= len(words):
                    next_pattern = tuple(words[j:j + ngram_size])
                    if next_pattern == pattern:
                        repeat_count += 1
                        j += ngram_size
                    else:
                        break
                
                # min_repeat 이상 반복되면 중복 제거 대상
                if repeat_count >= self.min_repeat:
                    # 첫 번째 패턴만 남기고 나머지 제거
                    for k in range(i + ngram_size, j):
                        to_remove.add(k)
                        removed_mask[k] = True
                    
                    # 패턴이 발견된 전체 구간을 건너뜀
                    i = j
                else:
                    i += 1
        
        return to_remove
    
    def remove_duplicates(self, text: str) -> str:
        """중복 제거된 텍스트 반환"""
        words = self.tokenize(text)
        
        if len(words) < self.min_repeat:
            return text
        
        to_remove = self.find_consecutive_repeats(words)
        
        # 제거할 인덱스를 제외하고 재구성
        result_words = [word for i, word in enumerate(words) if i not in to_remove]
        
        return ' '.join(result_words)
    
    def analyze(self, text: str) -> dict:
        """중복 패턴 분석 결과 반환"""
        words = self.tokenize(text)
        to_remove = self.find_consecutive_repeats(words)
        
        return {
            'original_length': len(words),
            'deduplicated_length': len(words) - len(to_remove),
            'removed_count': len(to_remove),
            'reduction_rate': f"{len(to_remove) / len(words) * 100:.1f}%" if words else "0%"
        }

def modify_sharp(text: str) -> str:
    """
    마크다운 헤더의 중복된 '#' 기호를 정리합니다.
    sed 명령어의 기능을 Python 정규식으로 구현합니다.
    """
    # s/^### ## /### /g 및 s/^### ### /### /g
    text = re.sub(r'^(###) ## ', r'\1 ', text, flags=re.MULTILINE)
    text = re.sub(r'^(###) ### ', r'\1 ', text, flags=re.MULTILINE)
    # s/^#### ### /#### /g 및 s/^#### #### /#### /g
    text = re.sub(r'^(####) ### ', r'\1 ', text, flags=re.MULTILINE)
    text = re.sub(r'^(####) #### ', r'\1 ', text, flags=re.MULTILINE)
    # s/^##### ### /##### /g
    text = re.sub(r'^(#####) ### ', r'\1 ', text, flags=re.MULTILINE)
    return text


def process_markdown_files_in_parent_directory():
    """
    Finds all markdown files in the parent directory, merges consecutive
    duplicate words, and overwrites the original files with the result.
    """
    # Get the absolute path of the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Get the parent directory
    parent_dir = os.path.dirname(script_dir)
    
    # Create a search pattern for markdown files in the parent directory
    search_pattern = os.path.join(parent_dir, '*.md')
    
    # Find all files matching the pattern
    markdown_files = glob.glob(search_pattern)
    
    if not markdown_files:
        print("No markdown files found in the parent directory.")
        return
        
    for filepath in markdown_files:
        print(f"Processing {filepath}...")
        process_file(filepath, filepath)

# 파일 처리 버전
def process_file(input_file, output_file):
    deduplicator = TextDeduplicator(min_repeat=3, max_ngram=30)
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    text_filter1 = deduplicator.remove_duplicates(text)
    """
  # 
  sed -i '' 's/^### ## /### /g' "$file"
  sed -i '' 's/^### ### /### /g' "$file"
  sed -i '' 's/^#### ### /#### /g' "$file"
  sed -i '' 's/^#### #### /#### /g' "$file"
  sed -i '' 's/^##### ### /##### /g' "$file"
    """
    cleaned_text = modify_sharp(text_filter1)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(cleaned_text)
    
    print(f"처리 완료: {input_file} -> {output_file}")


if __name__ == "__main__":
    process_markdown_files_in_parent_directory()