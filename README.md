# Maplee

Maplee는 독립 픽셀 액션 RPG입니다. 솔방울 마을, 종꽃 숲길, 푸른돛 항구, 유리빛 광산, 달바람 고원을 탐험하며 사냥, 전직, 제작, 퀘스트를 즐길 수 있습니다.

[웹에서 플레이](https://maplee-pixel-world.jisung-20090725.chatgpt.site)

## 실행

Python 3.10 이상에서 아래 명령을 실행한 뒤 `dist/index.html`을 브라우저에서 엽니다. 빌드가 처음에는 고정 버전의 Brython을 내려받고 체크섬을 확인합니다. 생성된 폴더에는 브라우저에서 Python을 실행하는 런타임과 모든 이미지가 포함됩니다.

```sh
python build.py
```

소스 폴더를 직접 실행하려면 `python -m http.server 8000`을 실행하고 `http://localhost:8000`을 엽니다. 소스 실행에서는 런타임을 불러오기 위해 인터넷이 필요합니다.

| 조작 | 키 |
| --- | --- |
| 이동 · 점프 | ← → · Space |
| 대화·출구·사다리 | ↑ · 사다리 내려가기는 ↓ |
| 발판 내려가기 | ↓ + Space |
| 기본 공격·주력 스킬·보조 스킬 | Z · X · V |
| 능력치·스킬·장비 | C · S · I |
| 퀘스트·지도·도감 | Q · M · B |
| 퀵슬롯·마을 귀환·저장 | 1~4 · R · K |

상태창과 장비창을 열어도 게임은 계속됩니다. 일시정지 버튼으로만 멈출 수 있습니다. 호스팅 버전은 ChatGPT로 인증하고 세이브는 현재 브라우저에 저장합니다.

## 소스와 검사

- `maplee/engine.py`는 물리, 전투, 몬스터 AI, 진행을 담당합니다.
- `maplee/render.py`와 `maplee/ui.py`는 Python으로 캔버스, 화면, 입력을 제어합니다. HTML·CSS와 Brython 실행용 로더를 사용합니다.
- `tools/draw_hero.py`, `tools/draw_gear.py`로 딱딱한 픽셀 경계의 원본 스프라이트를 재생성할 수 있습니다. 재생성 스크립트는 Pillow를 사용합니다.
- `python -m unittest discover -s tests`로 맵, 타격 타이밍, 보스 드롭, 제작, 세이브 호환성을 검사합니다.
