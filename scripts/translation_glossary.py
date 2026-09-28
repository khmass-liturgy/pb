"""번역 용어집 — 이 저장소의 모든 번역 스크립트가 공유한다.

fetch_briefing_news.py(해외 양계질병 뉴스)·fetch_poultry_diseases.py(The Poultry
Site 질병 자료)·fetch_research_papers.py(PubMed 논문 요약)가 각자 구글 번역
무료 엔드포인트·MyMemory·Claude API로 영→한 번역을 하는데, 그 결과가 국내 수의·
방역 현장에서 실제로 쓰는 용어와 다른 경우가 있다(예: "bird flu"를 기계번역하면
"조류독감"이 되지만, 국내 가축전염병예방법·방역 현장에서는 "조류인플루엔자"가
정식 명칭이다). 번역 API 자체에는 용어집 기능이 없어(무료 엔드포인트라 커스터마
이징 불가) 번역이 끝난 한글 텍스트에 사후로 용어를 바꿔치기한다.

새 용어를 고치거나 추가할 때는 이 파일 하나만 고치면 세 스크립트 전체(제목·
본문·요약)에 한 번에 적용된다. 각 스크립트에서는:
    from translation_glossary import apply_glossary
    ko = apply_glossary(translate(en, session))
처럼 번역 직후에 한 번만 통과시키면 된다.
"""

# (틀린/현장에서 안 쓰는 표현, 올바른 표현) 순서. 리스트 순서가 중요하다 — 긴
# 복합어를 먼저 넣어야 짧은 표현이 그 안쪽만 먼저 바꿔 의미가 어긋나는 일이
# 없다(예: "저병원성 조류독감"을 통째로 먼저 바꿔야 하고, "조류독감"만 있었어도
# 이 경우는 결과가 같지만 나중에 추가할 복합어는 순서에 따라 결과가 달라질 수
# 있어 원칙으로 남겨둔다).
GLOSSARY = [
    ("고병원성 조류독감", "고병원성 조류인플루엔자"),
    ("저병원성 조류독감", "저병원성 조류인플루엔자"),
    ("조류독감", "조류인플루엔자"),
]

# 받침 유무에 따라 형태가 갈리는 조사 쌍: (받침 있을 때 쓰는 형태, 받침 없을 때
# 쓰는 형태). "은/는"·"을/를"·"과/와"만 다룬다("이/가"는 아래에서 따로 다룬다) —
# 그 밖의 어미까지 다루면 오탐이 늘어나 위험 대비 이득이 적다. "으로/로"는
# 받침이 있어도 종성이 ㄹ이면 "로"를 쓰는 예외가 있어 별도로 처리한다.
_PARTICLE_PAIRS = [("은", "는"), ("을", "를"), ("과", "와")]

_HANGUL_BASE = 0xAC00
_HANGUL_LAST = 0xD7A3
_JONGSEONG_RIEUL = 8  # 종성 테이블(0=받침 없음)에서 ㄹ의 인덱스


def _is_hangul_syllable(ch):
    return bool(ch) and _HANGUL_BASE <= ord(ch) <= _HANGUL_LAST


def _has_batchim(word):
    """word 마지막 글자의 받침 유무. 한글 음절이 아니면(숫자·영문 등) 조사를
    함부로 바꾸지 않도록 보수적으로 "받침 있음"으로 본다."""
    if not word or not _is_hangul_syllable(word[-1]):
        return True
    return (ord(word[-1]) - _HANGUL_BASE) % 28 != 0


def _ends_in_rieul(word):
    if not word or not _is_hangul_syllable(word[-1]):
        return False
    return (ord(word[-1]) - _HANGUL_BASE) % 28 == _JONGSEONG_RIEUL


def _fix_trailing_particle(text, pos, new_word):
    """text[pos:]가 new_word 뒤에 바로 이어지는 조사로 시작하면, new_word의
    받침 유무에 맞는 조사 형태와 그 길이를 돌려준다. 조사가 아니면 (None, 0)."""
    if pos >= len(text):
        return None, 0
    has_batchim = _has_batchim(new_word)
    if text[pos:pos + 2] == "으로":
        use_ro = (not has_batchim) or _ends_in_rieul(new_word)
        return ("로" if use_ro else "으로"), 2
    ch = text[pos]
    if ch == "로":
        use_ro = (not has_batchim) or _ends_in_rieul(new_word)
        return ("로" if use_ro else "으로"), 1
    if ch == "이":
        nxt = text[pos + 1] if pos + 1 < len(text) else ""
        if _is_hangul_syllable(nxt):
            # 뒤 음절과 붙어 있으면 주격조사가 아니라 서술격조사 "이-"
            # (이다·이라는·이고·이며 등)다. 받침 없는 말 뒤에서는 이 "이"가
            # 통째로 줄어든다("이라는"→"라는") — 받침 있으면 그대로 둔다.
            return (None, 0) if has_batchim else ("", 1)
        # 뒤가 공백이거나 문장 끝 — 독립된 주격조사 "이/가"
        return ("이" if has_batchim else "가"), 1
    for with_batchim, without_batchim in _PARTICLE_PAIRS:
        if ch in (with_batchim, without_batchim):
            return (with_batchim if has_batchim else without_batchim), 1
    return None, 0


def apply_glossary(text):
    """번역된 한글 텍스트에 용어집을 적용한다. 뒤에 붙은 조사(이/가·은/는·을/를·
    과/와·으로/로)가 있으면 바뀐 단어의 받침에 맞는 형태로 함께 고친다
    ("조류독감이" → "조류인플루엔자가").

    text가 없거나(None) 빈 문자열이면 그대로 돌려준다 — 번역 실패로 호출부가
    원문(영문)이나 None을 그대로 쓰는 경로와 섞여도 안전하도록.
    """
    if not text:
        return text
    for wrong, right in GLOSSARY:
        idx = 0
        while True:
            i = text.find(wrong, idx)
            if i == -1:
                break
            end = i + len(wrong)
            new_particle, old_len = _fix_trailing_particle(text, end, right)
            if new_particle is not None:
                text = text[:i] + right + new_particle + text[end + old_len:]
                idx = i + len(right) + len(new_particle)
            else:
                text = text[:i] + right + text[end:]
                idx = i + len(right)
    return text
