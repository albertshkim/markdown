import streamlit as st
from datetime import datetime
import re
import json
import os

# 페이지 설정
st.set_page_config(page_title="AI Response Archiver", layout="wide", page_icon="🤖")

# --- 파일 저장 관리 함수 ---
DB_FILE = "recent_docs.json"

def load_recent_docs():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_to_recent(title, tags, content):
    docs = load_recent_docs()
    # 제목을 키로 저장 (최신순 정렬을 위해 시간 정보 포함)
    docs[title] = {
        "tags": tags,
        "content": content,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    # 최근 10개만 유지
    if len(docs) > 10:
        sorted_docs = dict(sorted(docs.items(), key=lambda x: x[1]['updated_at'], reverse=True)[:10])
        docs = sorted_docs
        
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=4)

# --- 유틸리티 함수: 마크다운 파싱 ---
def parse_markdown(content):
    title_match = re.search(r'^#\s+(.*)', content, re.MULTILINE)
    title = title_match.group(1) if title_match else "제목 없음"
    tag_match = re.search(r'>\s+\*\*태그:\*\*\s+(.*)', content)
    tags = tag_match.group(1) if tag_match else ""
    parts = content.split("---", 1)
    body = parts[1].strip() if len(parts) > 1 else content
    return title, tags, body

# --- 전체 화면 보기 팝업 ---
@st.dialog("전체 화면 보기", width="large")
def show_full_screen(title, content):
    st.markdown(f"# {title}")
    st.markdown(content)

# --- 세션 상태 초기화 ---
if "doc_title" not in st.session_state: st.session_state.doc_title = ""
if "tags" not in st.session_state: st.session_state.tags = ""
if "raw_content" not in st.session_state: st.session_state.raw_content = ""

# --- 사이드바: 최근 문서 리스트 ---
with st.sidebar:
    st.title("📂 최근 작업 문서")
    recent_docs = load_recent_docs()
    
    if recent_docs:
        # 최신순으로 정렬하여 표시
        sorted_titles = sorted(recent_docs.keys(), key=lambda x: recent_docs[x]['updated_at'], reverse=True)
        for t in sorted_titles:
            if st.button(f"📄 {t}", use_container_width=True, help=f"최종 수정: {recent_docs[t]['updated_at']}"):
                st.session_state.doc_title = t
                st.session_state.tags = recent_docs[t]['tags']
                st.session_state.raw_content = recent_docs[t]['content']
                st.rerun()
    else:
        st.write("최근 기록이 없습니다.")
    
    if st.button("🗑️ 기록 모두 삭제"):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
            st.rerun()

# --- 메인 화면 ---
st.title("🤖 AI 답변 마크다운 보관함")

uploaded_file = st.file_uploader("마크다운(.md) 파일을 드래그하여 불러오세요", type=["md"])
if uploaded_file is not None:
    stringio = uploaded_file.getvalue().decode("utf-8")
    u_title, u_tags, u_body = parse_markdown(stringio)
    st.session_state.doc_title = u_title
    st.session_state.tags = u_tags
    st.session_state.raw_content = u_body
    # 불러오자마자 최근 리스트에 저장
    save_to_recent(u_title, u_tags, u_body)

# 레이아웃 구성
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📥 내용 편집")
    doc_title = st.text_input("문서 제목", value=st.session_state.doc_title)
    tags = st.text_input("태그", value=st.session_state.tags)
    raw_content = st.text_area("본문 내용", value=st.session_state.raw_content, height=500)
    
    # [수정] 내보내기 버튼 클릭 시 최근 리스트에도 업데이트됨
    formatted_save = f"# {doc_title}\n\n> **작성일:** {datetime.now().strftime('%Y-%m-%d')}  \n> **태그:** {tags}\n\n---\n\n{raw_content}"
    
    if st.download_button("📥 수정된 파일 바로 내보내기", data=formatted_save, 
                          file_name=f"{doc_title}.md", mime="text/markdown", use_container_width=True):
        save_to_recent(doc_title, tags, raw_content)

with col2:
    st.subheader("👁️ 미리보기")
    v_col1, v_col2 = st.columns([1, 1])
    with v_col1:
        show_summary = st.checkbox("🔍 요약본 보기")
    with v_col2:
        if st.button("🖥️ Full화면으로 보기", use_container_width=True):
            show_full_screen(doc_title, raw_content)
    
    st.markdown("---")
    if show_summary and raw_content:
        st.info("\n".join(raw_content.split('\n')[:5]) + "...")
    st.markdown(f"# {doc_title}")
    st.markdown(raw_content)

# 하단 수동 저장 버튼 추가
if st.button("💾 현재 내용 최근 리스트에 저장하기", use_container_width=True):
    save_to_recent(doc_title, tags, raw_content)
    st.toast("최근 리스트에 저장되었습니다!")
