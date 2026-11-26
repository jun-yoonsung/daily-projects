"""시뮬레이션 결과를 외부 의존성 없는 단일 HTML 파일로 만든다."""

from __future__ import annotations

from html import escape

from .data import League
from .sim import SimResult

CSS = """
:root{--bg:#f4f6f3;--card:#fff;--ink:#1d2a22;--muted:#5d6b62;--line:#d5ddd6;--acc:47,125,74;--red:179,71,31}
@media (prefers-color-scheme:dark){:root{--bg:#101612;--card:#18211b;--ink:#e3ece5;--muted:#9aaba0;--line:#2c3a31;--acc:79,174,111;--red:255,138,92}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:system-ui,"Apple SD Gothic Neo","Malgun Gothic",sans-serif;line-height:1.5}
main{max-width:1000px;margin:0 auto;padding:24px 16px 40px}
h1{margin:0 0 4px;font-size:1.5rem}h2{font-size:1.1rem;margin:28px 0 8px}
p.meta{margin:0;color:var(--muted);font-size:.9rem}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px;overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:.85rem;font-variant-numeric:tabular-nums}
th,td{padding:5px 6px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}
th:nth-child(2),td:nth-child(2){text-align:left}
td.bar{min-width:120px}
.b{display:inline-block;height:9px;border-radius:2px;background:rgb(var(--acc));vertical-align:middle;margin-right:6px}
.b.r{background:rgb(var(--red))}
.heat td{text-align:center;min-width:38px;font-size:.75rem}
.heat td.n{text-align:left}
.heat th{text-align:center}.heat th:first-child{text-align:left}
.note{color:var(--muted);font-size:.85rem}
"""


def _bar(p: float, cls: str = "") -> str:
    width = round(p * 80)
    return f'<span class="b {cls}" style="width:{width}px"></span>{p * 100:.1f}%'


def render_html(league: League, result: SimResult, title: str = "시즌 시뮬레이션 리포트") -> str:
    ranked = result.ranked_ids()
    k = len(ranked)
    rows = []
    for i, t in enumerate(ranked, start=1):
        rows.append(
            "<tr>"
            f"<td>{i}</td><td>{escape(league.name_of(t))}</td>"
            f"<td>{result.current_points[t]}</td><td>{result.remaining_games[t]}</td>"
            f"<td>{result.mean_points[t]:.1f}</td>"
            f'<td class="bar">{_bar(result.title_prob[t])}</td>'
            f'<td class="bar">{_bar(result.top4_prob[t])}</td>'
            f'<td class="bar">{_bar(result.releg_prob[t], "r")}</td>'
            "</tr>"
        )
    heat_head = "".join(f"<th>{p}</th>" for p in range(1, k + 1))
    heat_rows = []
    for t in ranked:
        cells = []
        for p in result.pos_dist[t]:
            alpha = min(1.0, p * 1.6)
            color = "#fff" if alpha > 0.55 else "inherit"
            txt = f"{p * 100:.0f}" if p >= 0.005 else ""
            cells.append(
                f'<td style="background:rgba(var(--acc),{alpha:.3f});color:{color}">{txt}</td>'
            )
        heat_rows.append(f'<tr><td class="n">{escape(league.name_of(t))}</td>{"".join(cells)}</tr>')

    seed = "없음" if result.seed is None else str(result.seed)
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)}</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>{escape(title)}</h1>
<p class="meta">남은 경기 {len(league.remaining)}개 · {result.n:,}회 시뮬레이션 · seed {escape(seed)} · 상위 {result.top_n}팀 진출 / 하위 {result.releg_n}팀 강등 · 가상 데이터</p>

<h2>최종 순위 확률</h2>
<div class="card">
<table>
<thead><tr><th>#</th><th>팀</th><th>현재 승점</th><th>남은 경기</th><th>예상 승점</th><th>우승</th><th>상위 {result.top_n}</th><th>강등</th></tr></thead>
<tbody>
{chr(10).join(rows)}
</tbody>
</table>
</div>

<h2>순위 분포 (%)</h2>
<div class="card">
<table class="heat">
<thead><tr><th>팀</th>{heat_head}</tr></thead>
<tbody>
{chr(10).join(heat_rows)}
</tbody>
</table>
</div>
<p class="note">각 칸은 해당 팀이 그 순위로 시즌을 마칠 확률입니다. 색이 진할수록 확률이 높습니다. 모든 팀과 경기 결과는 가상 데이터입니다.</p>
</main>
</body>
</html>
"""
