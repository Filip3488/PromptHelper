import os
import re
import duckdb
import streamlit as st
from collections import defaultdict
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / "var.env")

TOKEN    = os.environ["MOTHERDUCK_TOKEN"]
DATABASE = os.getenv("MD_DATABASE", "PromptHelper")
TABLE    = os.getenv("MD_TABLE", "prompts")

C_ID          = os.getenv("COL_ID",          "id")
C_TITLE       = os.getenv("COL_TITLE",       "title")
C_CATEGORY    = os.getenv("COL_CATEGORY",    "category")
C_CONTENT     = os.getenv("COL_CONTENT",     "content")
C_DESCRIPTION = os.getenv("COL_DESCRIPTION", "description")
C_CREATED_AT  = os.getenv("COL_CREATED_AT",  "created_at")

CONN_STR = f"md:{DATABASE}?motherduck_token={TOKEN}"


def extract_variables(template: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r"\{(\w+)\}", template)))


def load_prompts() -> list[dict]:
    con = duckdb.connect(CONN_STR, read_only=True)
    rows = con.execute(
        f"SELECT {C_ID}, {C_TITLE}, {C_CATEGORY}, {C_CONTENT}, {C_DESCRIPTION} "
        f"FROM {TABLE} ORDER BY {C_CATEGORY}, {C_TITLE}"
    ).fetchall()
    con.close()
    return [{"id": r[0], "title": r[1], "category": r[2], "body": r[3], "description": r[4]} for r in rows]


st.set_page_config(page_title="Prompt Helper", layout="centered")
st.title("Prompt Helper")
st.markdown("<div style='margin-bottom: 2rem'></div>", unsafe_allow_html=True)

st.markdown("""
<style>
div.stButton > button {
    height: 3rem;
    font-size: 1.05rem;
}
[data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    align-items: center !important;
}
[data-testid="stHorizontalBlock"] [data-testid="stColumn"] {
    min-width: 4rem !important;
}
</style>
""", unsafe_allow_html=True)

prompts = load_prompts()

if not prompts:
    st.info("No prompts found in the database.")
    st.stop()

if "active" not in st.session_state:
    st.session_state.active = None
if "edit_preview" not in st.session_state:
    st.session_state.edit_preview = False

by_category = defaultdict(list)
for i, prompt in enumerate(prompts):
    by_category[prompt["category"]].append((i, prompt))
categories = sorted(by_category.keys())

all_tabs = st.tabs(["+ Add new prompt"] + categories)
add_tab = all_tabs[0]
category_tabs = all_tabs[1:]

# --- Add new prompt tab ---
with add_tab:
    new_title    = st.text_input("Title")
    new_category = st.text_input("Category")
    new_content  = st.text_area("Content", height=300)

    if st.button("Save to database", use_container_width=True):
        if not new_title.strip() or not new_category.strip() or not new_content.strip():
            st.warning("Please fill in all fields before saving.")
        else:
            import datetime
            con = duckdb.connect(CONN_STR)
            next_id = (con.execute(f"SELECT COALESCE(MAX({C_ID}), 0) FROM {TABLE}").fetchone()[0] or 0) + 1
            con.execute(
                f"INSERT INTO {TABLE} ({C_ID}, {C_TITLE}, {C_CATEGORY}, {C_CONTENT}, {C_CREATED_AT}) "
                f"VALUES (?, ?, ?, ?, ?)",
                [next_id, new_title.strip(), new_category.strip(), new_content.strip(), datetime.datetime.now()]
            )
            con.close()
            st.success(f'Prompt "{new_title}" saved.')
            st.rerun()

# --- Category tabs ---
for tab, category in zip(category_tabs, categories):
    with tab:
        for i, prompt in by_category[category]:
            col1, col2 = st.columns([5, 1], vertical_alignment="center")
            col1.markdown(f"**{prompt['title']}**")
            if col2.button("Use", key=f"use_{i}", use_container_width=True):
                st.session_state.active = i
                st.session_state.vars = {}
                st.session_state.edit_preview = False
            st.divider()

        if st.session_state.active is not None and prompts[st.session_state.active]["category"] == category:
            prompt = prompts[st.session_state.active]
            st.subheader(prompt["title"])

            if prompt.get("description"):
                st.caption(prompt["description"])

            variables = extract_variables(prompt["body"])

            if variables:
                st.markdown("Fill in the variables:")
                for var in variables:
                    col_label, col_input = st.columns([1, 3], vertical_alignment="center")
                    col_label.markdown(f"**{var}**")
                    st.session_state.vars[var] = col_input.text_input(
                        var,
                        value=st.session_state.vars.get(var, ""),
                        key=f"var_{var}",
                        label_visibility="collapsed",
                    )
            else:
                st.info("This prompt has no variables.")

            filled = prompt["body"]
            for var in variables:
                val = st.session_state.vars.get(var, f"{{{var}}}")
                filled = filled.replace(f"{{{var}}}", val)

            prev_col, btn_col = st.columns([5, 1], vertical_alignment="center")
            prev_col.markdown("**Preview**")
            edit_label = "Lock" if st.session_state.edit_preview else "Edit"
            if btn_col.button(edit_label, key=f"toggle_edit_{st.session_state.active}", use_container_width=True):
                st.session_state.edit_preview = not st.session_state.edit_preview

            if st.session_state.edit_preview:
                filled = st.text_area("Edit prompt", value=filled, height=300, label_visibility="collapsed", key=f"preview_edit_{st.session_state.active}")
            else:
                if f"preview_edit_{st.session_state.active}" in st.session_state:
                    filled = st.session_state.get(f"preview_edit_{st.session_state.active}", filled)
                st.markdown(filled.replace("\n", "  \n"))

            with st.expander("Copy"):
                st.code(filled, language=None)