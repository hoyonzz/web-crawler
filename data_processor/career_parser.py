import re



def parse_career_from_header(text: str) -> list[str] | None:
    """
    헤더의 구조화된 경력 표기를 룰로 확정 파싱.
    패턴을 못 찾으면 None반환
    """
    if '[상단 요약 정보]' not in text:
        return None
    
    header_zone = text.split('[상세 본문]')[0]
    
    result = set()

    m = re.search(r'경력\s*(\d+)\s*[-~]\s*(\d+)\s*년', header_zone)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        if lo == 0:
            result.add('신입')
        if lo <= 2 and hi >= 1:
            result.add('1~2년')
        if hi >= 3:
            result.add('3년이상')

    m = re.search(r'경력\s*(\d+)\s*년\s*이상', header_zone)
    if m:
        lo = int(m.group(1))
        if lo <= 2:
            result.add("1~2년")
        result.add("3년이상")

    if re.search(r'신입', header_zone):
        result.add('신입')
    
    if re.search(r'경력\s*무관', header_zone):
        result.add('경력무관')

    return sorted(result) if result else None