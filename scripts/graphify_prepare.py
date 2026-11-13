#!/usr/bin/env python3
"""index.html 안의 인라인 <script>를 graphify가 읽을 수 있는 JS 파일로 뽑는다.

graphify는 .html 속 JS를 분석하지 못하므로 `graphify update .` 전에 이 스크립트를 먼저 실행한다.
출력 줄 번호 = index.html 줄 번호(스크립트 밖 줄은 빈 줄)라 그래프의 loc=L123 이 index.html 줄과 같다.
data URI 같은 매우 긴 줄(>1500자)은 구조 분석에 필요 없어 짧은 주석으로 줄인다.
사용: python scripts/graphify_prepare.py && graphify update .
"""
import os
import re

SRC, DST = "index.html", "graphify-src/index.inline.js"
LONG = 1500

out, inside = [], False
for ln in open(SRC, encoding="utf-8").read().split("\n"):
    if not inside:
        m = re.search(r"<script(\s[^>]*)?>", ln)
        if m and "src=" not in m.group(0) and "ld+json" not in m.group(0):
            ln = ln[m.end():]
            if "</script>" in ln:
                out.append(ln.split("</script>")[0])
                continue
            inside = True
            out.append(ln)
            continue
        out.append("")
    else:
        if "</script>" in ln:
            out.append(ln.split("</script>")[0])
            inside = False
        else:
            out.append(ln)

out = ["/* long line omitted */" if len(l) > LONG else l for l in out]
os.makedirs(os.path.dirname(DST), exist_ok=True)
with open(DST, "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print(f"{DST}: {len(out)} lines")
