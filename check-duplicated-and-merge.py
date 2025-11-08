import os
import re
from pathlib import Path
from collections import defaultdict

class RollingHash:
    """Rabin-Karp 알고리즘을 위한 Rolling Hash 구현"""
    def __init__(self, text, window_size):
        self.text = text
        self.window_size = window_size
        self.base = 256
        self.mod = 10**9 + 7
        self.base_power = pow(self.base, window_size - 1, self.mod)
        
    def compute_hash(self, s):
        """문자열의 해시값 계산"""
        h = 0
        for char in s:
            h = (h * self.base + ord(char)) % self.mod
        return h
    
    def roll(self, old_hash, old_char, new_char):
        """O(1) 시간에 해시값 업데이트"""
        old_hash = (old_hash - ord(old_char) * self.base_power) % self.mod
        old_hash = (old_hash * self.base + ord(new_char)) % self.mod
        return old_hash

def has_korean(text):
    """텍스트에 한글이 포함되어 있는지 확인"""
    return bool(re.search(r'[가-힣]', text))

def find_repeating_patterns_rolling_hash(text, min_pattern_len=10, max_pattern_len=100):
    """
    Rolling Hash를 사용하여 반복 패턴 찾기 (한글만 처리)
    """
    if len(text) < min_pattern_len * 3:
        return text
    
    result = text
    
    # 여러 길이의 패턴을 검사 (긴 것부터 - 더 큰 중복을 먼저 제거)
    for pattern_len in range(max_pattern_len, min_pattern_len - 1, -5):
        if len(result) < pattern_len * 3:
            continue
            
        changed = True
        max_iterations = 3
        iteration = 0
        
        while changed and iteration < max_iterations:
            changed = False
            iteration += 1
            
            # 해시값과 위치를 저장
            hash_positions = defaultdict(list)
            rh = RollingHash(result, pattern_len)
            
            # 첫 번째 윈도우의 해시 계산
            if len(result) >= pattern_len:
                current_hash = rh.compute_hash(result[:pattern_len])
                hash_positions[current_hash].append(0)
                
                # Rolling Hash로 나머지 윈도우 처리
                for i in range(1, len(result) - pattern_len + 1):
                    current_hash = rh.roll(
                        current_hash,
                        result[i - 1],
                        result[i + pattern_len - 1]
                    )
                    hash_positions[current_hash].append(i)
            
            # 3회 이상 반복되는 패턴 찾기
            to_remove = []
            for hash_val, positions in hash_positions.items():
                if len(positions) >= 3:
                    # 실제로 같은 문자열인지 확인 (해시 충돌 방지)
                    pattern = result[positions[0]:positions[0] + pattern_len]
                    
                    # 한글이 포함된 패턴만 처리
                    if not has_korean(pattern):
                        continue
                    
                    # 연속된 반복인지 확인
                    consecutive_groups = []
                    current_group = [positions[0]]
                    
                    for i in range(1, len(positions)):
                        # 패턴 길이만큼 떨어져 있으면 연속으로 간주
                        if positions[i] - current_group[-1] <= pattern_len + 10:  # 약간의 여유
                            if result[positions[i]:positions[i] + pattern_len] == pattern:
                                current_group.append(positions[i])
                        else:
                            if len(current_group) >= 3:
                                consecutive_groups.append(current_group)
                            current_group = [positions[i]]
                    
                    if len(current_group) >= 3:
                        consecutive_groups.append(current_group)
                    
                    # 연속된 반복 그룹 제거 대상에 추가
                    for group in consecutive_groups:
                        if len(group) >= 3:
                            start = group[0]
                            end = group[-1] + pattern_len
                            to_remove.append((start, end, pattern))
            
            # 제거 대상을 뒤에서부터 처리 (인덱스 변경 방지)
            to_remove.sort(reverse=True)
            for start, end, pattern in to_remove:
                # 반복 구간을 하나의 패턴으로 교체
                result = result[:start] + pattern + result[end:]
                changed = True
    
    return result

def simple_replace_cleanup(text):
    """
    단순 문자열 치환으로 불필요한 패턴 제거
    """
    replacements = [
        (r'\s*\[음악\]\s*', ' '),
        (r'\s*\[박수\]\s*', ' '),
        (r'\s*\[Music\]\s*', ' '),
        (" [음악] ", " "),
        (" [박수] ", " "),
        (" [Music] ", " "),
        (" 으 ", " "),
        (" 아 ", " "),
        (" 카 ", " "),
        (" 켈 ", " "),
    ]
    
    result = text
    for old, new in replacements:
        result = result.replace(old, new)
    
    return result

def find_and_merge_repetitions(text):
    """
    텍스트에서 3회 이상 연속 반복되는 한글 단어나 문장을 찾아서 하나로 병합합니다.
    영어/URL 등은 보존됩니다.
    Rolling Hash와 정규식을 조합한 하이브리드 방식.
    """
    # 0단계: 단순 치환 먼저 수행
    result = simple_replace_cleanup(text)
    
    # 1단계: 한글만 공백 없이 붙어있는 반복 처리
    # 예: "세계세계세계" -> "세계"
    # 한글 유니코드 범위: [\uAC00-\uD7A3]
    result = re.sub(r'([\uAC00-\uD7A3]{2,}?)\1{2,}', r'\1', result)
    
    # 2단계: 한글 단어의 공백으로 구분된 반복 (최소 2글자 이상의 단어만)
    # 예: "세계 세계 세계" -> "세계"
    # 단, 줄 시작의 리스트 마커는 제외
    result = re.sub(r'(?<![*\-+])\s+([\uAC00-\uD7A3]{2,})(?:\s+\1){2,}(?![*\-+])', r' \1', result)
    
    # 3단계: Rolling Hash로 중간 길이 한글 패턴 처리 (10-100자)
    # 긴 한글 문장이나 구절의 반복을 효율적으로 찾음
    result = find_repeating_patterns_rolling_hash(result, min_pattern_len=15, max_pattern_len=100)
    
    # 4단계: 매우 긴 한글 반복 (100자 이상)
    # 한글이 포함된 긴 패턴만 처리
    lines = result.split('\n')
    processed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if len(line) >= 100 and has_korean(line):
            # 같은 줄이 3번 이상 연속되는지 확인
            repeat_count = 1
            while i + repeat_count < len(lines) and lines[i + repeat_count] == line:
                repeat_count += 1
            
            if repeat_count >= 3:
                processed_lines.append(line)
                i += repeat_count
            else:
                processed_lines.append(line)
                i += 1
        else:
            processed_lines.append(line)
            i += 1
    
    result = '\n'.join(processed_lines)
    
    return result


def process_markdown_file(filepath):
    """
    마크다운 파일을 읽고, 반복을 제거한 후, 같은 파일에 저장합니다.
    """
    try:
        # 파일 읽기
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 너무 큰 파일은 건너뛰기 (10MB 이상)
        if len(content) > 10 * 1024 * 1024:
            print(f"파일이 너무 큽니다. 건너뜀: {filepath} ({len(content)} bytes)")
            return False
        
        # 반복 제거
        processed_content = find_and_merge_repetitions(content)
        
        # 변경사항이 있는 경우에만 파일 쓰기
        if content != processed_content:
            reduction = len(content) - len(processed_content)
            reduction_pct = (reduction / len(content)) * 100 if len(content) > 0 else 0
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(processed_content)
            print(f"✓ 처리 완료: {filepath} (감소: {reduction} bytes, {reduction_pct:.1f}%)")
            return True
        else:
            print(f"○ 변경사항 없음: {filepath}")
            return False
            
    except Exception as e:
        print(f"✗ 오류 발생 ({filepath}): {e}")
        return False


def main():
    """
    현재 디렉터리와 모든 하위 디렉터리의 .md 파일을 처리합니다.
    """
    current_dir = Path('.')
    md_files = list(current_dir.glob('**/*.md'))
    
    if not md_files:
        print("현재 디렉터리 및 하위 디렉터리에 .md 파일이 없습니다.")
        return
    
    print(f"총 {len(md_files)}개의 .md 파일을 찾았습니다.")
    print("-" * 60)
    
    processed_count = 0
    total_reduction = 0
    
    for i, md_file in enumerate(md_files, 1):
        print(f"[{i}/{len(md_files)}] ", end="")
        if process_markdown_file(md_file):
            processed_count += 1
    
    print("-" * 60)
    print(f"완료: {processed_count}개 파일 수정됨, {len(md_files) - processed_count}개 파일 변경사항 없음")


if __name__ == "__main__":
    import time
    start_time = time.time()
    main()
    elapsed = time.time() - start_time
    print(f"\n총 소요 시간: {elapsed:.2f}초 (파일당 평균 {elapsed/70:.2f}초)" if elapsed > 0 else "\n완료!")