import streamlit as st
from datetime import datetime
import re
import json
import os
import subprocess
import platform
import streamlit.components.v1 as components

st.set_page_config(page_title="AI Response Archiver", layout="wide", page_icon="🤖")

st.markdown("""
<style>
.toc-item {
    display:block; color:#ffffff !important; text-decoration:none;
    padding:5px 8px; border-radius:6px; margin:2px 0;
    line-height:1.5; cursor:pointer;
    transition:all 0.18s ease;
    border-left:2px solid transparent;
}
.toc-item:hover { background:rgba(233,69,96,0.12); border-left-color:#e94560; }
.toc-badge {
    display:inline-block; font-size:10px; font-weight:700;
    padding:1px 6px; border-radius:10px; margin-right:6px;
    min-width:22px; text-align:center;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# 비밀번호 설정
# ══════════════════════════════════════════════════════════
# APP_PASSWORD = "123" + datetime.now().strftime("%Y%m%d") + "1"
APP_PASSWORD = "123" + datetime.now().strftime("%d") + "1"
MAX_ATTEMPTS = 2

if "auth_ok"       not in st.session_state: st.session_state.auth_ok       = False
if "auth_attempts" not in st.session_state: st.session_state.auth_attempts = 0
if "auth_blocked"  not in st.session_state: st.session_state.auth_blocked  = False

# ── 차단 화면 ─────────────────────────────────────────────
if st.session_state.auth_blocked:
    st.markdown("""
    <div style="display:flex;flex-direction:column;align-items:center;
                justify-content:center;height:70vh;">
      <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);
                  border:2px solid #e94560;border-radius:20px;
                  padding:50px 60px;text-align:center;max-width:420px;">
        <div style="font-size:60px;margin-bottom:16px;">🚫</div>
        <h2 style="color:#e94560;margin-bottom:12px;">접근이 차단되었습니다</h2>
        <p style="color:#8892b0;font-size:15px;line-height:1.7;">
          비밀번호를 2회 이상 틀렸습니다.<br>애플리케이션이 종료되었습니다.
        </p>
        <div style="background:rgba(233,69,96,0.1);border-radius:10px;
                    padding:12px 20px;margin-top:20px;color:#e94560;font-size:13px;">
          페이지를 새로고침하여 다시 시도하세요.
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── 로그인 화면 ───────────────────────────────────────────
if not st.session_state.auth_ok:
    remaining = MAX_ATTEMPTS - st.session_state.auth_attempts

    st.markdown("""
    <div style="display:flex;justify-content:center;padding-top:80px;">
      <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);
                  border:1px solid #0f3460;border-radius:20px;
                  padding:50px 60px;text-align:center;max-width:440px;width:100%;
                  box-shadow:0 20px 60px rgba(0,0,0,0.5);">
        <div style="font-size:56px;margin-bottom:12px;">🔐</div>
        <h2 style="color:#e2e8f8;margin-bottom:6px;">AI 답변 마크다운 보관함</h2>
        <p style="color:#8892b0;font-size:14px;margin-bottom:0;">
          접근하려면 비밀번호를 입력하세요
        </p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    _, mid, _ = st.columns([1, 1.1, 1])
    with mid:
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        if st.session_state.auth_attempts > 0:
            st.markdown(
                f'<div style="background:rgba(233,69,96,0.12);border:1px solid #e94560;'
                f'border-radius:8px;padding:10px 16px;margin-bottom:10px;'
                f'color:#e94560;font-size:13px;text-align:center;">'
                f'⚠️ 비밀번호가 틀렸습니다. 남은 시도: <strong>{remaining}회</strong></div>',
                unsafe_allow_html=True)
        pw = st.text_input("비밀번호", type="password",
                           placeholder="비밀번호를 입력하세요",
                           label_visibility="collapsed")
        if st.button("🔓 입장하기", use_container_width=True, type="primary"):
            if pw == APP_PASSWORD:
                st.session_state.auth_ok = True
                st.rerun()
            else:
                st.session_state.auth_attempts += 1
                if st.session_state.auth_attempts >= MAX_ATTEMPTS:
                    st.session_state.auth_blocked = True
                st.rerun()
    st.stop()


# ══════════════════════════════════════════════════════════
# 인증 통과 후 메인 앱
# ══════════════════════════════════════════════════════════

# ── 파일 관리 ─────────────────────────────────────────────
DB_FILE    = "recent_docs.json"
EXPORT_DIR = os.path.abspath("exported_docs")
os.makedirs(EXPORT_DIR, exist_ok=True)

def load_recent_docs():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_to_recent(title, tags, content):
    docs = load_recent_docs()
    docs[title] = {"tags": tags, "content": content,
                   "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    if len(docs) > 10:
        docs = dict(sorted(docs.items(), key=lambda x: x[1]['updated_at'], reverse=True)[:10])
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=4)

def get_export_file_path(title):
    safe = re.sub(r'[\\/*?:"<>|]', "_", title)
    return os.path.join(EXPORT_DIR, f"{safe}.md")

def save_file_to_disk(title, tags, content):
    fmt = (f"# {title}\n\n> **작성일:** {datetime.now().strftime('%Y-%m-%d')}  \n"
           f"> **태그:** {tags}\n\n---\n\n{content}")
    path = get_export_file_path(title)
    with open(path, "w", encoding="utf-8") as f:
        f.write(fmt)
    return path

def open_in_explorer(path):
    sys = platform.system()
    try:
        if sys == "Windows":
            subprocess.Popen(f'explorer /select,"{path}"' if os.path.isfile(path)
                             else f'explorer "{os.path.dirname(path)}"')
        elif sys == "Darwin":
            subprocess.Popen(["open", "-R", path] if os.path.isfile(path)
                             else ["open", os.path.dirname(path)])
        else:
            subprocess.Popen(["xdg-open",
                              os.path.dirname(path) if os.path.isfile(path) else path])
        return True
    except Exception as e:
        return str(e)

# ── 마크다운 유틸 ─────────────────────────────────────────
def parse_markdown(content):
    t = re.search(r'^#\s+(.*)', content, re.MULTILINE)
    g = re.search(r'>\s+\*\*태그:\*\*\s+(.*)', content)
    parts = content.split("---", 1)
    return (t.group(1) if t else "제목 없음",
            g.group(1) if g else "",
            parts[1].strip() if len(parts) > 1 else content)

def make_anchor(text, idx):
    a = re.sub(r'[^\w가-힣\s-]', '', text.lower())
    a = re.sub(r'\s+', '-', a.strip())
    return f"h{idx}-{a}"

def extract_headings(content):
    headings, idx = [], 0
    for line in content.split('\n'):
        m = re.match(r'^(#{1,4})\s+(.*)', line)
        if m:
            headings.append({'level': len(m.group(1)), 'text': m.group(2).strip(),
                             'anchor': make_anchor(m.group(2).strip(), idx), 'idx': idx})
            idx += 1
    return headings

def inline_md(text, is_dark=True):
    tc    = "#e2e8f8" if is_dark else "#1a1a2a"
    lc    = "#7b8cde" if is_dark else "#2563eb"
    cc_bg = "#2d2d3d" if is_dark else "#f0f0f5"
    cc_cl = "#e94560" if is_dark else "#c7254e"
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
    text = re.sub(r'\*\*(.+?)\*\*', f'<strong style="color:{tc}">\\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'`(.+?)`',
        f'<code style="background:{cc_bg};color:{cc_cl};padding:2px 6px;'
        f'border-radius:4px;font-size:0.88em">\\1</code>', text)
    text = re.sub(r'\[(.+?)\]\((.+?)\)',
        f'<a href="\\2" style="color:{lc};text-decoration:underline">\\1</a>', text)
    return text

def md_to_html_with_anchors(content, headings, is_dark=True):
    if is_dark:
        bg       = "linear-gradient(160deg,#0d1117 0%,#141824 100%)"
        h_colors = {1:"#e2e8f8",2:"#c8d0f0",3:"#9ba8cc",4:"#7888b0"}
        h_borders= {1:"border-bottom:2px solid #e94560;padding-bottom:8px;",
                    2:"border-bottom:1px solid #1e2d50;padding-bottom:5px;",3:"",4:""}
        h_hash_c = {1:"#e94560",2:"#7b8cde",3:"#5fb7d4",4:"#8ecf8e"}
        bq_bg="#rgba(233,69,96,0.05)"; bq_bl="#e94560"; bq_c="#8892b0"
        code_bg="#0d1117"; code_bd="#30363d"; code_c="#e6edf3"
        hr_c="#1e2d50"; li_c="#a8b2d8"; p_c="#a8b2d8"
        title_c="#e2e8f8"; title_bd="#e94560"
    else:
        bg       = "#ffffff"
        h_colors = {1:"#0f172a",2:"#1e293b",3:"#334155",4:"#475569"}
        h_borders= {1:"border-bottom:2px solid #2563eb;padding-bottom:8px;",
                    2:"border-bottom:1px solid #cbd5e1;padding-bottom:5px;",3:"",4:""}
        h_hash_c = {1:"#2563eb",2:"#7c3aed",3:"#0891b2",4:"#059669"}
        bq_bg="rgba(37,99,235,0.05)"; bq_bl="#2563eb"; bq_c="#64748b"
        code_bg="#f8f8f8"; code_bd="#e2e8f0"; code_c="#1e293b"
        hr_c="#e2e8f0"; li_c="#1e293b"; p_c="#334155"
        title_c="#0f172a"; title_bd="#2563eb"

    lines = content.split('\n')
    out, hidx = [], 0
    in_code, code_buf, code_lang = False, [], ""
    in_ul, in_ol = False, False

    def close_lists():
        nonlocal in_ul, in_ol
        res = []
        if in_ul: res.append('</ul>'); in_ul = False
        if in_ol: res.append('</ol>'); in_ol = False
        return res

    for line in lines:
        if line.startswith("```"):
            out.extend(close_lists())
            if not in_code:
                in_code, code_lang, code_buf = True, line[3:].strip(), []
            else:
                in_code = False
                esc = "\n".join(code_buf).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
                lbl = (f'<span style="color:#e94560;font-size:10px;float:right;opacity:.7">'
                       f'{code_lang}</span>') if code_lang else ''
                out.append(f'<pre style="background:{code_bg};border:1px solid {code_bd};'
                           f'color:{code_c};padding:14px;border-radius:8px;overflow-x:auto;'
                           f'font-size:13px;margin:12px 0">{lbl}<code>{esc}</code></pre>')
            continue
        if in_code:
            code_buf.append(line); continue

        hm = re.match(r'^(#{1,4})\s+(.*)', line)
        if hm:
            out.extend(close_lists())
            lv   = len(hm.group(1)); text = hm.group(2).strip()
            anch = headings[hidx]['anchor'] if hidx < len(headings) else f"h{hidx}"; hidx += 1
            sz   = {1:"1.9em",2:"1.45em",3:"1.2em",4:"1.05em"}[lv]
            hpx  = {1:"#",2:"##",3:"###",4:"####"}[lv]
            out.append(f'<h{lv} id="{anch}" style="font-size:{sz};color:{h_colors[lv]};'
                       f'margin:1.3em 0 0.4em;{h_borders[lv]}scroll-margin-top:60px">'
                       f'<span style="color:{h_hash_c[lv]};font-size:0.65em;margin-right:8px;'
                       f'opacity:0.8">{hpx}</span>{text}</h{lv}>')
            continue

        if re.match(r'^-{3,}$', line.strip()):
            out.extend(close_lists())
            out.append(f'<hr style="border:none;border-top:1px solid {hr_c};margin:16px 0">'); continue

        if line.startswith('> '):
            out.extend(close_lists())
            inner = inline_md(line[2:], is_dark)
            out.append(f'<blockquote style="border-left:3px solid {bq_bl};padding:6px 14px;'
                       f'color:{bq_c};margin:10px 0;background:{bq_bg};border-radius:0 6px 6px 0">'
                       f'{inner}</blockquote>'); continue

        bm = re.match(r'^[-*+]\s+(.*)', line)
        if bm:
            if not in_ul:
                out.extend(close_lists())
                out.append(f'<ul style="padding-left:22px;margin:6px 0;color:{li_c}">'); in_ul = True
            out.append(f'<li style="color:{li_c};margin:3px 0;line-height:1.7">'
                       f'{inline_md(bm.group(1), is_dark)}</li>'); continue

        nm = re.match(r'^\d+\.\s+(.*)', line)
        if nm:
            if not in_ol:
                out.extend(close_lists())
                out.append(f'<ol style="padding-left:22px;margin:6px 0;color:{li_c}">'); in_ol = True
            out.append(f'<li style="color:{li_c};margin:3px 0;line-height:1.7">'
                       f'{inline_md(nm.group(1), is_dark)}</li>'); continue

        if not line.strip():
            out.extend(close_lists()); out.append('<div style="height:8px"></div>'); continue

        out.extend(close_lists())
        out.append(f'<p style="color:{p_c};line-height:1.75;margin:4px 0">'
                   f'{inline_md(line, is_dark)}</p>')

    out.extend(close_lists())
    return bg, title_c, title_bd, "\n".join(out)

# ── 목차 렌더링 (공통 함수) ───────────────────────────────
def render_toc(headings):
    if not headings:
        st.markdown(
            '<div style="background:linear-gradient(135deg,#1a1a2e,#16213e);'
            'border:1px solid #0f3460;border-radius:12px;padding:20px;text-align:center;'
            'color:#ffffff;font-size:12px;font-style:italic">'
            '헤딩(#)이 없습니다.<br># 제목을 추가하면 목차가 자동 생성됩니다.'
            '</div>', unsafe_allow_html=True)
        return

    BADGE_COLOR = {1:"#e94560",2:"#7b8cde",3:"#5fb7d4",4:"#8ecf8e"}
    BADGE_LABEL = {1:"H1",2:"H2",3:"H3",4:"H4"}
    INDENT      = {1:0,2:14,3:28,4:42}
    FSIZE       = {1:14,2:13,3:12,4:11}
    FWEIGHT     = {1:700,2:600,3:400,4:400}

    items_html = []
    for h in headings:
        lv   = h['level']
        disp = h['text'][:38]+"…" if len(h['text'])>40 else h['text']
        bc   = BADGE_COLOR.get(lv,"#a8b2d8")
        items_html.append(
            f'<div class="item" style="margin-left:{INDENT.get(lv,0)}px;'
            f'font-size:{FSIZE.get(lv,12)}px;font-weight:{FWEIGHT.get(lv,400)};color:#f0f4ff" '
            f'onclick="tocClick(\'{h["anchor"]}\')" title="{h["text"]}">'
            f'<span class="badge" style="background:{bc}33;color:{bc}">'
            f'{BADGE_LABEL.get(lv,"H?")}</span>{disp}</div>'
        )

    n          = len(headings)
    toc_height = min(56 + n * 34, 400)
    toc_html   = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:transparent;overflow:hidden;font-family:'Segoe UI','Noto Sans KR',sans-serif}}
.wrap{{background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);border:1px solid #0f3460;
       border-radius:12px;padding:14px;height:{toc_height}px;overflow-y:auto}}
.wrap::-webkit-scrollbar{{width:4px}}
.wrap::-webkit-scrollbar-thumb{{background:#0f3460;border-radius:4px}}
.hdr{{color:#e94560;font-size:10px;font-weight:700;letter-spacing:3px;text-transform:uppercase;
      margin-bottom:10px;padding-bottom:8px;border-bottom:1px solid #0f3460}}
.item{{display:block;color:#f0f4ff;padding:5px 8px;border-radius:6px;margin:2px 0;
       line-height:1.5;cursor:pointer;transition:background .18s,border-left-color .18s;
       border-left:2px solid transparent;user-select:none}}
.item:hover{{color:#ffc8d0;background:rgba(233,69,96,.14);border-left-color:#e94560}}
.badge{{display:inline-block;font-size:10px;font-weight:700;padding:1px 6px;
        border-radius:10px;margin-right:6px;min-width:22px;text-align:center}}
</style></head><body>
<div class="wrap">
  <div class="hdr">📑 TABLE OF CONTENTS</div>
  {''.join(items_html)}
</div>
<script>
function tocClick(id){{
  function tryScroll(w){{
    try{{
      const el=w.document.getElementById(id);
      if(el){{
        el.scrollIntoView({{behavior:'smooth',block:'start'}});
        el.style.transition='background 0.1s';
        el.style.background='rgba(233,69,96,.18)';
        setTimeout(()=>{{el.style.transition='background 1.8s ease';
                         el.style.background='transparent';}},200);
        return true;
      }}
    }}catch(e){{}}return false;
  }}
  if(tryScroll(window))return;
  if(tryScroll(window.parent))return;
  try{{
    const fs=window.parent.document.querySelectorAll('iframe');
    for(const f of fs){{if(tryScroll(f.contentWindow))return;}}
  }}catch(e){{}}
}}
</script></body></html>"""
    components.html(toc_html, height=toc_height + 6, scrolling=False)
    st.caption("💡 목차 클릭 시 오른쪽 미리보기의 해당 섹션으로 이동합니다.")

# ── 다이얼로그 ────────────────────────────────────────────
@st.dialog("전체 화면 보기", width="large")
def show_full_screen(title, content):
    st.markdown(f"# {title}")
    st.markdown(content)

@st.dialog("📁 파일 경로 탐색", width="large")
def show_file_path_dialog(title, tags, content):
    fpath  = get_export_file_path(title)
    fdir   = os.path.dirname(fpath)
    exists = os.path.isfile(fpath)
    st.markdown("### 📄 현재 문서 경로 정보")
    st.markdown("**📂 저장 폴더**"); st.code(fdir, language="")
    st.markdown("**📄 파일 전체 경로**"); st.code(fpath, language="")
    if exists:
        st.success("✅ 파일이 디스크에 존재합니다.")
        c1, c2 = st.columns(2)
        c1.metric("최종 수정일",
                  datetime.fromtimestamp(os.path.getmtime(fpath)).strftime("%Y-%m-%d %H:%M:%S"))
        c2.metric("파일 크기", f"{os.path.getsize(fpath):,} bytes")
    else:
        st.warning("⚠️ 아직 디스크에 저장되지 않았습니다.")
    st.divider()
    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("💾 저장 후 탐색기 열기", use_container_width=True, type="primary"):
            p = save_file_to_disk(title, tags, content)
            save_to_recent(title, tags, content)
            r = open_in_explorer(p)
            st.success("✅ 완료!") if r is True else st.error(f"실패: {r}")
    with b2:
        if st.button("📂 저장 폴더 열기", use_container_width=True):
            r = open_in_explorer(fdir)
            st.success("✅ 열었습니다.") if r is True else st.error(f"실패: {r}")
    with b3:
        if st.button("📋 경로 복사", use_container_width=True):
            st.text_input("Ctrl+A → Ctrl+C:", value=fpath)
    st.caption("💡 탐색기 열기는 로컬 환경에서만 동작합니다.")

@st.dialog("🗑️ 현재 문서 삭제", width="small")
def confirm_delete_current():
    dt = st.session_state.doc_title
    st.markdown(
        f'<div style="background:rgba(233,69,96,0.08);border:1px solid rgba(233,69,96,0.35);'
        f'border-radius:10px;padding:16px 18px;margin-bottom:16px;text-align:center">'
        f'<div style="font-size:36px;margin-bottom:8px">🗑️</div>'
        f'<div style="color:#e94560;font-size:15px;font-weight:700;margin-bottom:6px">'
        f'"{dt if dt else "제목 없음"}"</div>'
        f'<div style="color:#8892b0;font-size:13px;line-height:1.6">'
        f'현재 열린 문서를 화면에서 삭제합니다.<br>'
        f'최근 목록에서도 제거됩니다.</div></div>',
        unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ 삭제 확인", use_container_width=True, type="primary"):
            # 최근 목록에서 제거
            docs = load_recent_docs()
            if dt in docs:
                del docs[dt]
                with open(DB_FILE, "w", encoding="utf-8") as f:
                    json.dump(docs, f, ensure_ascii=False, indent=4)
            # 세션 초기화
            st.session_state.doc_title   = ""
            st.session_state.tags        = ""
            st.session_state.raw_content = ""
            st.session_state.scroll_anchor = None
            st.rerun()
    with c2:
        if st.button("❌ 취소", use_container_width=True):
            st.rerun()

# ── 세션 초기화 (앱 상태) ─────────────────────────────────
for k, v in [("doc_title", ""), ("tags", ""), ("raw_content", ""),
             ("scroll_anchor", None), ("toc_expanded", True), ("preview_dark", True),
             ("left_view_mode", "전체화면 보기")]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── 사이드바 ─────────────────────────────────────────────
with st.sidebar:
    st.title("📂 최근 작업 문서")
    recent_docs = load_recent_docs()
    if recent_docs:
        for t in sorted(recent_docs, key=lambda x: recent_docs[x]['updated_at'], reverse=True):
            if st.button(f"📄 {t}", use_container_width=True,
                         help=f"최종 수정: {recent_docs[t]['updated_at']}"):
                st.session_state.update(
                    doc_title=t, tags=recent_docs[t]['tags'],
                    raw_content=recent_docs[t]['content'], scroll_anchor=None)
                st.rerun()
    else:
        st.write("최근 기록이 없습니다.")
    if st.button("🗑️ 기록 모두 삭제"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE); st.rerun()

# ── 메인 타이틀 ──────────────────────────────────────────
st.title("🤖 AI 답변 마크다운 보관함")

uploaded_file = st.file_uploader("마크다운(.md) 파일을 드래그하여 불러오세요", type=["md"])
if uploaded_file:
    u_title, u_tags, u_body = parse_markdown(uploaded_file.getvalue().decode("utf-8"))
    st.session_state.update(doc_title=u_title, tags=u_tags,
                            raw_content=u_body, scroll_anchor=None)
    save_to_recent(u_title, u_tags, u_body)

col1, col2 = st.columns([1, 1])

# ═══════════════════════════════════════════════════════════
# 왼쪽 컬럼
# ═══════════════════════════════════════════════════════════
with col1:

    # ── 화면 보기 옵션 ────────────────────────────────────
    st.markdown("##### 📐 화면 보기 옵션")
    seg1, seg2 = st.columns(2)
    cur_mode   = st.session_state.left_view_mode

    with seg1:
        is_full = cur_mode == "전체화면 보기"
        if st.button("🖥️ 전체화면 보기", use_container_width=True,
                     type="primary" if is_full else "secondary", key="btn_view_full"):
            st.session_state.left_view_mode = "전체화면 보기"
            st.rerun()
    with seg2:
        is_edit = cur_mode == "편집화면 보기"
        if st.button("✏️ 편집화면 보기", use_container_width=True,
                     type="primary" if is_edit else "secondary", key="btn_view_edit"):
            st.session_state.left_view_mode = "편집화면 보기"
            st.rerun()

    if cur_mode == "전체화면 보기":
        st.markdown(
            '<div style="background:rgba(233,69,96,0.08);border:1px solid rgba(233,69,96,0.3);'
            'border-radius:6px;padding:5px 12px;font-size:12px;color:#e94560;margin:6px 0 4px">'
            '🖥️ <strong>전체화면 보기</strong> — 문서 정보 및 목차를 표시합니다</div>',
            unsafe_allow_html=True)
    else:
        st.markdown(
            '<div style="background:rgba(123,140,222,0.08);border:1px solid rgba(123,140,222,0.3);'
            'border-radius:6px;padding:5px 12px;font-size:12px;color:#7b8cde;margin:6px 0 4px">'
            '✏️ <strong>편집화면 보기</strong> — 편집 및 저장 기능을 표시합니다</div>',
            unsafe_allow_html=True)

    st.markdown("---")

    # ── 전체화면 보기 모드 ───────────────────────────────
    if cur_mode == "전체화면 보기":
        st.subheader("📄 문서 정보")

        dt = st.session_state.doc_title
        tg = st.session_state.tags
        if dt:
            st.markdown(
                f'<div style="background:linear-gradient(135deg,#1a1a2e,#16213e);'
                f'border:1px solid #0f3460;border-radius:10px;padding:14px 18px;margin-bottom:10px">'
                f'<div style="color:#8892b0;font-size:11px;margin-bottom:4px">📌 문서 제목</div>'
                f'<div style="color:#e2e8f8;font-size:16px;font-weight:700">{dt}</div></div>',
                unsafe_allow_html=True)
        if tg:
            st.markdown(
                f'<div style="background:linear-gradient(135deg,#1a1a2e,#16213e);'
                f'border:1px solid #0f3460;border-radius:10px;padding:10px 18px;margin-bottom:10px">'
                f'<div style="color:#8892b0;font-size:11px;margin-bottom:4px">🏷️ 태그</div>'
                f'<div style="color:#7b8cde;font-size:13px">{tg}</div></div>',
                unsafe_allow_html=True)
        if not dt:
            st.info("✏️ 편집화면 보기 모드에서 내용을 입력하거나 파일을 불러오세요.")

        # ── 현재 문서 삭제 버튼 (전체화면 모드) ──────────────
        if dt:
            if st.button("🗑️ 현재 문서 삭제", use_container_width=True, key="del_full"):
                confirm_delete_current()

        st.markdown("---")
        headings = extract_headings(st.session_state.raw_content)
        n = len(headings)
        tc1, tc2 = st.columns([5, 1])
        with tc1:
            st.markdown(
                f'**📑 전체 목차** '
                f'<span style="background:#0f3460;color:#e94560;padding:2px 9px;'
                f'border-radius:10px;font-size:11px;font-weight:700">{n}개</span>',
                unsafe_allow_html=True)
        with tc2:
            lbl = "접기 ▲" if st.session_state.toc_expanded else "펼치기 ▼"
            if st.button(lbl, key="toc_toggle_full", use_container_width=True):
                st.session_state.toc_expanded = not st.session_state.toc_expanded
                st.rerun()
        if st.session_state.toc_expanded:
            render_toc(headings)

    # ── 편집화면 보기 모드 ───────────────────────────────
    else:
        st.subheader("📥 내용 편집")
        doc_title   = st.text_input("문서 제목", value=st.session_state.doc_title)
        tags        = st.text_input("태그",      value=st.session_state.tags)
        raw_content = st.text_area("본문 내용",  value=st.session_state.raw_content, height=400)

        # 편집값 즉시 세션 반영
        st.session_state.doc_title   = doc_title
        st.session_state.tags        = tags
        st.session_state.raw_content = raw_content

        fmt_save = (f"# {doc_title}\n\n> **작성일:** {datetime.now().strftime('%Y-%m-%d')}  \n"
                    f"> **태그:** {tags}\n\n---\n\n{raw_content}")
        dl_col, del_col = st.columns([3, 1])
        with dl_col:
            if st.download_button("📥 수정된 파일 바로 내보내기", data=fmt_save,
                                  file_name=f"{doc_title}.md", mime="text/markdown",
                                  use_container_width=True):
                save_to_recent(doc_title, tags, raw_content)
        with del_col:
            if st.button("🗑️ 삭제", use_container_width=True,
                         key="del_edit", disabled=not bool(doc_title)):
                confirm_delete_current()

        st.markdown("---")
        headings = extract_headings(raw_content)
        n = len(headings)
        tc1, tc2 = st.columns([5, 1])
        with tc1:
            st.markdown(
                f'**📑 전체 목차** '
                f'<span style="background:#0f3460;color:#e94560;padding:2px 9px;'
                f'border-radius:10px;font-size:11px;font-weight:700">{n}개</span>',
                unsafe_allow_html=True)
        with tc2:
            lbl = "접기 ▲" if st.session_state.toc_expanded else "펼치기 ▼"
            if st.button(lbl, key="toc_toggle_edit", use_container_width=True):
                st.session_state.toc_expanded = not st.session_state.toc_expanded
                st.rerun()
        if st.session_state.toc_expanded:
            render_toc(headings)

# ═══════════════════════════════════════════════════════════
# 오른쪽 컬럼: 미리보기
# ═══════════════════════════════════════════════════════════
with col2:
    st.subheader("👁️ 미리보기")

    vc1, vc2, vc3 = st.columns([1, 1, 1])
    with vc1:
        if st.button("🖥️ Full화면으로 보기", use_container_width=True):
            show_full_screen(st.session_state.doc_title, st.session_state.raw_content)
    with vc2:
        if st.button("📁 경로 보기", use_container_width=True):
            show_file_path_dialog(st.session_state.doc_title,
                                  st.session_state.tags,
                                  st.session_state.raw_content)
    with vc3:
        is_dark   = st.session_state.preview_dark
        theme_lbl = "☀️ 라이트 모드" if is_dark else "🌙 다크 모드"
        if st.button(theme_lbl, use_container_width=True):
            st.session_state.preview_dark = not is_dark
            st.rerun()

    is_dark = st.session_state.preview_dark
    if is_dark:
        st.markdown(
            '<div style="background:#0d1117;border:1px solid #30363d;border-radius:6px;'
            'padding:5px 12px;font-size:12px;color:#8892b0;margin-bottom:4px">'
            '🌙 <strong style="color:#a8b2d8">다크 모드</strong> — 검정 배경 / 흰색 계열 글자</div>',
            unsafe_allow_html=True)
    else:
        st.markdown(
            '<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;'
            'padding:5px 12px;font-size:12px;color:#64748b;margin-bottom:4px">'
            '☀️ <strong style="color:#1e293b">라이트 모드</strong> — 흰색 배경 / 검정 계열 글자</div>',
            unsafe_allow_html=True)

    st.markdown("---")

    scroll_anchor              = st.session_state.scroll_anchor
    st.session_state.scroll_anchor = None
    raw_content                = st.session_state.raw_content
    doc_title                  = st.session_state.doc_title

    if raw_content:
        h_list = extract_headings(raw_content)
        bg, title_c, title_bd, body_html = md_to_html_with_anchors(raw_content, h_list, is_dark)

        scroll_js = ""
        if scroll_anchor:
            scroll_js = f"""<script>
window.addEventListener('DOMContentLoaded',function(){{
  setTimeout(function(){{
    const el=document.getElementById('{scroll_anchor}');
    if(el){{
      el.scrollIntoView({{behavior:'smooth',block:'start'}});
      el.style.background='rgba(233,69,96,0.15)';
      el.style.borderRadius='6px';
      el.style.transition='background 1.8s ease';
      setTimeout(()=>el.style.background='transparent',2000);
    }}
  }},80);
}});
</script>"""

        preview_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box}}
body{{font-family:'Segoe UI','Noto Sans KR',sans-serif;background:{bg};
     color:{'#a8b2d8' if is_dark else '#334155'};margin:0;padding:24px 28px;
     line-height:1.75;font-size:14px}}
h1,h2,h3,h4{{font-family:'Segoe UI',sans-serif}}
pre{{white-space:pre-wrap;word-break:break-all}}
ul,ol{{padding-left:22px;margin:6px 0}}
li{{margin:3px 0}}
a{{color:{'#7b8cde' if is_dark else '#2563eb'}}}
</style>{scroll_js}</head><body>
<h1 style="font-size:2em;color:{title_c};border-bottom:2px solid {title_bd};
           padding-bottom:10px;margin-bottom:16px">{doc_title}</h1>
{body_html}
</body></html>"""
        components.html(preview_html, height=1240, scrolling=True)
    else:
        st.markdown("*본문을 입력하면 미리보기가 표시됩니다.*")

# ── 하단 저장 ────────────────────────────────────────────
if st.button("💾 현재 내용 최근 리스트에 저장하기", use_container_width=True):
    save_to_recent(st.session_state.doc_title,
                   st.session_state.tags,
                   st.session_state.raw_content)
    st.toast("최근 리스트에 저장되었습니다!")
