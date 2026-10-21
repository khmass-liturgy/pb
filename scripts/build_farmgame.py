"""farmgame/game.html(닭 키우기 게임 원본)을 index.html의 FARMGAME_HTML 상수에 다시 넣는다.

게임을 고친 뒤 `python scripts/build_farmgame.py`를 실행하면 된다. 게임은 유료서비스 화면에서
iframe srcdoc으로 띄우므로(회원만 보이고, 사이트 CSS와 섞이지 않음) 별도 파일을 배포하지 않는다.
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
src = (ROOT / "farmgame" / "game.html").read_text(encoding="utf-8")
# </script> 등이 바깥 <script>를 닫지 않도록 "</"를 "<\/"로 바꾼다(JS 문자열에서는 같은 값).
literal = json.dumps(src, ensure_ascii=False).replace("</", "<\\/")
index = ROOT / "index.html"
html = index.read_text(encoding="utf-8")
line = f"const FARMGAME_HTML = {literal};"
new, n = re.subn(r"^const FARMGAME_HTML = .*;$", lambda m: line, html, count=1, flags=re.M)
if n != 1:
    raise SystemExit("index.html에서 'const FARMGAME_HTML = ...;' 줄을 찾지 못했습니다.")
index.write_text(new, encoding="utf-8")
print(f"FARMGAME_HTML 갱신: {len(src):,}자")
