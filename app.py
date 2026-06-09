import streamlit as st
import pandas as pd
from datetime import date
import io

# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="盤點行事曆調度管理系統",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  /* ── 最大化可用寬度 ── */
  .block-container {
      padding-top: 0.8rem !important;
      padding-bottom: 1rem !important;
      padding-left: 1.5rem !important;
      padding-right: 1.5rem !important;
      max-width: 100% !important;
  }

  /* ── 全域基礎字體放大 ── */
  html, body, [class*="css"] { font-size: 15px; }

  /* ── 標題 ── */
  h1 { font-size: 1.8rem !important; margin-bottom: 0.3rem !important; }
  h2 { font-size: 1.4rem !important; margin-bottom: 0.2rem !important; }
  h3 { font-size: 1.15rem !important; margin-bottom: 0.2rem !important; margin-top: 0 !important; }

  /* ── Metric ── */
  [data-testid="stMetricValue"] { font-size: 1.6rem !important; }
  [data-testid="stMetricLabel"] { font-size: 0.9rem !important; }

  /* ── 按鈕：放大文字 + 增加內距 + 固定最小高度 ── */
  [data-testid="stButton"] > button {
      font-size: 1rem !important;
      font-weight: 500 !important;
      padding: 0.5rem 0.8rem !important;
      min-height: 2.6rem !important;
      border-radius: 6px !important;
      width: 100% !important;
  }

  /* ── 輸入欄位 label 放大 ── */
  [data-testid="stSelectbox"] label,
  [data-testid="stDateInput"] label,
  [data-testid="stTextInput"] label,
  [data-testid="stCheckbox"] label,
  [data-testid="stFileUploader"] label {
      font-size: 0.95rem !important;
      font-weight: 500 !important;
  }

  /* ── selectbox / date_input 選項文字 ── */
  [data-testid="stSelectbox"] > div > div,
  [data-testid="stDateInput"] input {
      font-size: 0.95rem !important;
  }

  /* ── caption 字體 ── */
  [data-testid="stCaptionContainer"] p { font-size: 0.9rem !important; }

  /* ── 三欄間距 ── */
  div[data-testid="column"] > div { padding: 0 8px !important; }

  /* ── data_editor 圓角框 ── */
  [data-testid="stDataEditor"] { border-radius: 8px !important; }

  /* ── sidebar ── */
  [data-testid="stSidebar"] { font-size: 0.9rem !important; }
  [data-testid="stSidebar"] label { font-size: 0.9rem !important; }
  [data-testid="stSidebar"] [data-testid="stButton"] > button {
      font-size: 0.9rem !important;
      min-height: 2.2rem !important;
  }

  /* ── divider 間距縮小 ── */
  hr { margin: 0.5rem 0 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SCHEMA
#   _src : 'main' | 'left' | 'sample'   — data origin (used only for reload)
#   _loc : 'left' | 'middle' | 'right'  — current UI column (single source of
#                                          truth; all move ops only touch this)
#   _is_new : bool — True for user-added stores (drives 🔵 status)
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# DATE UTILITIES
# ─────────────────────────────────────────────────────────────────────────────
def _fmt_date(d) -> str:
    """Normalize any date value → 'YYYY-MM-DD' string; '暫存' passes through."""
    if d == "暫存":
        return "暫存"
    if isinstance(d, date):
        return d.strftime("%Y-%m-%d")
    try:
        ts = pd.Timestamp(d)
        if not pd.isnull(ts):
            return ts.strftime("%Y-%m-%d")
    except Exception:
        pass
    return ""


def _to_date(d) -> "date | None":
    """Convert any date-like value → Python datetime.date; None on failure."""
    if isinstance(d, date):
        return d
    try:
        ts = pd.Timestamp(d)
        if not pd.isnull(ts):
            return ts.date()
    except Exception:
        pass
    return None


def _col_str(series: pd.Series) -> pd.Series:
    """Convert a date column to 'YYYY-MM-DD' strings (type-safe comparison)."""
    return series.apply(_fmt_date)


def _min_date(df: pd.DataFrame) -> "date | None":
    """Return the earliest datetime.date in 目前日期 column, ignoring '暫存'."""
    vals = [_to_date(d) for d in df["目前日期"] if _fmt_date(d) != "暫存"]
    vals = [v for v in vals if v is not None]
    return min(vals) if vals else None


# ─────────────────────────────────────────────────────────────────────────────
# EXCEL PARSERS
# ─────────────────────────────────────────────────────────────────────────────
def _parse_main_excel(file) -> pd.DataFrame:
    """Parse INV_7_5 盤點行事曆_勤務行事曆報表.
    Row 7 (header=6). Required: 午別 日期 店號 店名 型態. Optional: 預定盤點者."""
    try:
        raw = pd.read_excel(file, header=6, dtype={"店號": str})
    except Exception as exc:
        raise ValueError(f"無法開啟 Excel 檔案。\n錯誤：{exc}")

    required = ["午別", "日期", "店號", "店名", "型態"]
    missing = [c for c in required if c not in raw.columns]
    if missing:
        raise ValueError(
            f"Excel 缺少必要欄位：{missing}\n"
            f"檔案中偵測到：{list(raw.columns)}"
        )

    df = raw[required].copy()
    df["日期"]  = pd.to_datetime(df["日期"], errors="coerce").dt.date
    df["店號"]  = df["店號"].astype(str).str.strip()
    for c in ["午別", "店名", "型態"]:
        df[c] = df[c].astype(str).str.strip()

    df["預定盤點者"] = (
        raw["預定盤點者"].astype(str).str.strip().replace("nan", "")
        if "預定盤點者" in raw.columns else ""
    )

    df = df.dropna(subset=["日期"])
    df = df[df["店號"].str.len() > 0]
    df = df[df["店號"] != "nan"]

    return pd.DataFrame({
        "店號":       df["店號"].values,
        "店名":       df["店名"].values,
        "型態":       df["型態"].values,
        "原始日期":   df["日期"].values,
        "原始班別":   df["午別"].values,
        "目前日期":   df["日期"].values,
        "目前班別":   df["午別"].values,
        "預定盤點者": df["預定盤點者"].values,
        "_src":       "main",
        "_is_new":    False,
        "_loc":       "middle",
    }).reset_index(drop=True)


def _parse_left_excel(file) -> pd.DataFrame:
    """Parse simple Excel for 異動店鋪 (left column).
    Standard header row. Required: 店號 店名 日期 班別. Optional: 型態."""
    try:
        raw = pd.read_excel(file, dtype={"店號": str})
    except Exception as exc:
        raise ValueError(f"無法開啟 Excel 檔案。\n錯誤：{exc}")

    required = ["店號", "店名", "日期", "班別"]
    missing = [c for c in required if c not in raw.columns]
    if missing:
        raise ValueError(
            f"Excel 缺少必要欄位：{missing}\n"
            f"檔案中偵測到：{list(raw.columns)}"
        )

    df = raw[required].copy()
    df["日期"] = pd.to_datetime(df["日期"], errors="coerce").dt.date
    df["店號"] = df["店號"].astype(str).str.strip()
    for c in ["店名", "班別"]:
        df[c] = df[c].astype(str).str.strip()
    df["型態"] = (
        raw["型態"].astype(str).str.strip()
        if "型態" in raw.columns else ""
    )

    df = df.dropna(subset=["日期"])
    df = df[df["店號"].str.len() > 0]
    df = df[df["店號"] != "nan"]

    return pd.DataFrame({
        "店號":       df["店號"].values,
        "店名":       df["店名"].values,
        "型態":       df["型態"].values,
        "原始日期":   df["日期"].values,
        "原始班別":   df["班別"].values,
        "目前日期":   df["日期"].values,
        "目前班別":   df["班別"].values,
        "預定盤點者": "",
        "_src":       "left",
        "_is_new":    True,
        "_loc":       "left",
    }).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────────────────────────────────────
def _build_sample_df() -> pd.DataFrame:
    """啟動時回傳空白 DataFrame（含欄位結構）。"""
    return pd.DataFrame(columns=[
        "店號", "店名", "型態", "原始日期", "原始班別",
        "目前日期", "目前班別", "預定盤點者",
        "_src", "_is_new", "_loc",
    ])


def _init_session():
    if "df" not in st.session_state:
        st.session_state.df = _build_sample_df()
    if "ev" not in st.session_state:
        st.session_state.ev = 0
    defaults = {
        "la_date":     date.today(),
        "la_show_all": False,
        "mb_date":     date.today(),
        "tgt_date":    date.today(),
        "tgt_shift":   "上午",
        "g_kw":        "",
        "g_rg":        "全選",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_session()


# ─────────────────────────────────────────────────────────────────────────────
# DATA OPERATIONS
# ─────────────────────────────────────────────────────────────────────────────
def _load_main(df_new: pd.DataFrame):
    """Replace main rows; preserve non-main rows. Auto-sets mb_date."""
    df_new = df_new.copy()
    df_new["_src"]    = "main"
    df_new["_is_new"] = False
    df_new["_loc"]    = "middle"
    keep = st.session_state.df[st.session_state.df["_src"] != "main"].copy()
    st.session_state.df = pd.concat([df_new, keep], ignore_index=True)
    st.session_state.ev += 1
    md = _min_date(df_new)
    if md:
        st.session_state.mb_date = md


def _load_left(df_new: pd.DataFrame):
    """Replace left rows; preserve non-left rows. Auto-sets la_date."""
    df_new = df_new.copy()
    df_new["_src"]    = "left"
    df_new["_is_new"] = True
    df_new["_loc"]    = "left"
    keep = st.session_state.df[st.session_state.df["_src"] != "left"].copy()
    st.session_state.df = pd.concat([keep, df_new], ignore_index=True)
    st.session_state.ev += 1
    md = _min_date(df_new)
    if md:
        st.session_state.la_date = md


def _add_manual(store_date, store_shift, store_id, store_name, store_type):
    """Add a single store to the left column."""
    new_row = pd.DataFrame([{
        "店號":       store_id,
        "店名":       store_name,
        "型態":       store_type,
        "原始日期":   store_date,
        "原始班別":   store_shift,
        "目前日期":   store_date,
        "目前班別":   store_shift,
        "預定盤點者": "",
        "_src":       "left",
        "_is_new":    True,
        "_loc":       "left",
    }])
    st.session_state.df = pd.concat(
        [st.session_state.df, new_row], ignore_index=True
    )
    st.session_state.ev += 1


# ── Move operations ──────────────────────────────────────────────────────────
# Each function only mutates _loc (+ date/shift as needed) and bumps ev.
# Because _loc is the single source of truth for which column a store appears
# in, changing it is all that's needed — the store vanishes from the old
# column and appears in the new one on the next rerun.

def _move_to_right(ids: list) -> bool:
    """Move stores to right column (暫存大水庫)."""
    if not ids:
        return False
    mask = st.session_state.df["店號"].isin(ids)
    st.session_state.df.loc[mask, "_loc"]    = "right"
    st.session_state.df.loc[mask, "目前日期"] = "暫存"
    st.session_state.df.loc[mask, "目前班別"] = "暫存"
    st.session_state.ev += 1
    return True


def _move_to_mid(ids: list, target_date: date) -> bool:
    """Move stores to middle column (現行班表) at target_date."""
    if not ids:
        return False
    mask = st.session_state.df["店號"].isin(ids)
    st.session_state.df.loc[mask, "_loc"]    = "middle"
    st.session_state.df.loc[mask, "目前日期"] = target_date
    new_mask = mask & (st.session_state.df["_is_new"] == True)
    st.session_state.df.loc[new_mask, "預定盤點者"] = "待重新指派"
    st.session_state.ev += 1
    return True


def _move_to_left(ids: list, target_date: date) -> bool:
    """Move stores to left column (異動店鋪) at target_date."""
    if not ids:
        return False
    mask = st.session_state.df["店號"].isin(ids)
    st.session_state.df.loc[mask, "_loc"]    = "left"
    st.session_state.df.loc[mask, "目前日期"] = target_date
    st.session_state.df.loc[mask, "_is_new"] = True
    st.session_state.ev += 1
    return True


def _assign_from_right(ids: list, target_date: date, target_shift: str) -> bool:
    """Assign stores from right (暫存) to middle (現行班表) with given date+shift."""
    if not ids:
        return False
    mask = st.session_state.df["店號"].isin(ids)
    st.session_state.df.loc[mask, "_loc"]      = "middle"
    st.session_state.df.loc[mask, "目前日期"]   = target_date
    st.session_state.df.loc[mask, "目前班別"]   = target_shift
    st.session_state.df.loc[mask, "預定盤點者"] = "待重新指派"
    st.session_state.ev += 1
    return True


def _apply_global(df: pd.DataFrame) -> pd.DataFrame:
    kw = st.session_state.get("g_kw", "").strip()
    rg = st.session_state.get("g_rg", "全選")
    if kw:
        m = (df["店號"].str.contains(kw, case=False, na=False) |
             df["店名"].str.contains(kw, case=False, na=False))
        df = df[m]
    if rg != "全選":
        df = df[df["型態"] == rg]
    return df


# ─────────────────────────────────────────────────────────────────────────────
# DISPLAY HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _edf_left(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "選取": False,
        "日期": df["目前日期"].apply(_fmt_date),
        "班別": df["目前班別"],
        "店號": df["店號"],
        "店名": df["店名"],
        "型態": df["型態"],
    }).reset_index(drop=True)


def _edf_mid(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "選取": False,
        "日期": df["目前日期"].apply(_fmt_date),
        "班別": df["目前班別"],
        "店號": df["店號"],
        "店名": df["店名"],
        "型態": df["型態"],
        "預定盤點者": df["預定盤點者"],
    }).reset_index(drop=True)


def _edf_right(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "選取": False,
        "店號": df["店號"],
        "店名": df["店名"],
        "型態": df["型態"],
    }).reset_index(drop=True)


def _get_ids(edited_df, src_df: pd.DataFrame) -> list:
    if edited_df is None or src_df.empty:
        return []
    try:
        return edited_df[edited_df["選取"] == True]["店號"].tolist()
    except Exception:
        return []


_CC_LEFT = {
    "選取": st.column_config.CheckboxColumn("選取", width="small"),
    "日期": st.column_config.TextColumn("日期",      width="medium"),
    "班別": st.column_config.TextColumn("班別",      width="small"),
    "店號": st.column_config.TextColumn("店號",      width="small"),
    "店名": st.column_config.TextColumn("店名"),
    "型態": st.column_config.TextColumn("型態",      width="small"),
}
_DIS_LEFT = ["日期", "班別", "店號", "店名", "型態"]

_CC_MID = {
    "選取":       st.column_config.CheckboxColumn("選取",    width="small"),
    "日期":       st.column_config.TextColumn("日期",         width="medium"),
    "班別":       st.column_config.TextColumn("班別",         width="small"),
    "店號":       st.column_config.TextColumn("店號",         width="small"),
    "店名":       st.column_config.TextColumn("店名"),
    "型態":       st.column_config.TextColumn("型態",         width="small"),
    "預定盤點者": st.column_config.TextColumn("預定盤點者"),
}
_DIS_MID = ["日期", "班別", "店號", "店名", "型態", "預定盤點者"]

_CC_RIGHT = {
    "選取": st.column_config.CheckboxColumn("選取", width="small"),
    "店號": st.column_config.TextColumn("店號",     width="small"),
    "店名": st.column_config.TextColumn("店名"),
    "型態": st.column_config.TextColumn("型態",     width="small"),
}
_DIS_RIGHT = ["店號", "店名", "型態"]


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR  —  IMPORT & MANUAL ADD
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("📂 資料匯入")

    st.subheader("1️⃣ 現行班表（中欄）")
    st.caption("來源：7.5盤點行程查詢 → 勤務行事曆報表\n第 7 列為標題，需含 午別/日期/店號/店名/型態")
    file_main = st.file_uploader("上傳 Excel", type=["xlsx", "xls"], key="up_main")
    if file_main:
        st.caption(f"📄 {file_main.name}")
        if st.button("✅ 確認載入現行班表", key="btn_main", use_container_width=True):
            with st.spinner("讀取中…"):
                try:
                    _load_main(_parse_main_excel(file_main))
                    st.success("✓ 成功載入")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

    st.divider()

    st.subheader("2️⃣ 異動店鋪（左欄）匯入 [選填]")
    st.caption("一般 Excel，第 1 列為標題，需含 店號/店名/日期/班別")
    file_left = st.file_uploader("上傳 Excel", type=["xlsx", "xls"], key="up_left")
    if file_left:
        st.caption(f"📄 {file_left.name}")
        if st.button("✅ 確認載入異動店鋪", key="btn_left", use_container_width=True):
            with st.spinner("讀取中…"):
                try:
                    _load_left(_parse_left_excel(file_left))
                    st.success("✓ 成功載入")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

    st.divider()

    st.subheader("➕ 手動新增異動店鋪")
    with st.form("add_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            f_date  = st.date_input("日期",  value=st.session_state.la_date)
        with c2:
            f_shift = st.selectbox("班別", ["上午", "下午"])
        f_id   = st.text_input("店號")
        f_name = st.text_input("店名")
        f_type = st.text_input("型態", placeholder="選填")
        submitted = st.form_submit_button("新增至左欄", use_container_width=True)
        if submitted:
            if f_id.strip() and f_name.strip():
                _add_manual(f_date, f_shift, f_id.strip(), f_name.strip(), f_type.strip())
                st.success(f"✓ 已新增 {f_id.strip()}")
                st.rerun()
            else:
                st.warning("店號與店名為必填")

    st.divider()

    st.caption("**目前資料統計**")
    _sc = st.session_state.df["_src"].value_counts().to_dict()
    if _sc.get("main", 0):
        st.caption(f"📅 現行班表：{_sc['main']} 筆")
    if _sc.get("left", 0):
        st.caption(f"📋 異動店鋪：{_sc['left']} 筆")
    if _sc.get("sample", 0):
        st.caption(f"📝 範例資料：{_sc.get('sample', 0)} 筆")
    _n_temp = int((st.session_state.df["_loc"] == "right").sum())
    if _n_temp:
        st.caption(f"🗄️ 暫存中：{_n_temp} 筆")

    st.divider()

    # ── 一鍵清除資料 ────────────────────────────────────────────────────────────
    st.caption("**⚠️ 危險操作**")
    if "confirm_clear" not in st.session_state:
        st.session_state.confirm_clear = False

    if not st.session_state.confirm_clear:
        if st.button("🗑️ 清除所有資料", use_container_width=True):
            st.session_state.confirm_clear = True
            st.rerun()
    else:
        st.warning("確定要清除全部資料嗎？此操作無法復原。")
        _cc1, _cc2 = st.columns(2)
        with _cc1:
            if st.button("✅ 確認清除", use_container_width=True, type="primary"):
                # 重置為完全空白的 DataFrame（含欄位結構，不含任何資料）
                st.session_state.df = pd.DataFrame(columns=[
                    "店號", "店名", "型態", "原始日期", "原始班別",
                    "目前日期", "目前班別", "預定盤點者",
                    "_src", "_is_new", "_loc",
                ])
                st.session_state.ev = 0
                st.session_state.confirm_clear = False
                st.rerun()
        with _cc2:
            if st.button("❌ 取消", use_container_width=True):
                st.session_state.confirm_clear = False
                st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.title("🏪 盤點行事曆調度管理系統")

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL FILTERS
# ─────────────────────────────────────────────────────────────────────────────
gf1, gf2, gf3, gf4, gf5 = st.columns([3, 2, 1, 1, 1])
with gf1:
    st.text_input("🔍 關鍵字搜尋（店號 / 店名）", key="g_kw", placeholder="輸入關鍵字…")
with gf2:
    _all_types = ["全選"] + sorted(st.session_state.df["型態"].unique().tolist())
    if st.session_state.get("g_rg", "全選") not in _all_types:
        st.session_state["g_rg"] = "全選"
    st.selectbox("🏷️ 型態篩選", _all_types, key="g_rg")
with gf3:
    st.metric("總筆數", len(st.session_state.df))
with gf4:
    st.metric("暫存中", int((st.session_state.df["_loc"] == "right").sum()))
with gf5:
    _main_rows = st.session_state.df[st.session_state.df["_src"].isin(["main", "sample"])]
    _chg = int(
        ((_col_str(_main_rows["目前日期"]) != _col_str(_main_rows["原始日期"])) |
         (_main_rows["目前班別"] != _main_rows["原始班別"])).sum()
    )
    st.metric("現行異動", _chg)

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# MAIN LAYOUT : left panels (top / middle / bottom) + right comparison panel
# ─────────────────────────────────────────────────────────────────────────────
fdf = _apply_global(st.session_state.df)
ev  = st.session_state.ev

# Status computation (needed by both comparison panel and export)
def _compute_status(row) -> str:
    if row["_is_new"]:
        return "🔵 新增異動"
    if row["_loc"] == "right":
        return "🔴 暫存中"
    curr = _fmt_date(row["目前日期"])
    orig = _fmt_date(row["原始日期"])
    if orig == curr and row["原始班別"] == row["目前班別"]:
        return "🟢 未變動"
    return "🟡 已變更"

cdf = st.session_state.df.copy()
cdf["狀態"] = cdf.apply(_compute_status, axis=1)

col_panels, col_compare = st.columns([3, 1.4], gap="large")

# ═══ LEFT : THREE STACKED PANELS ═════════════════════════════════════════════
with col_panels:

    # ── TOP : 異動店鋪（預計要排的資料）──────────────────────────────────────────
    st.markdown("### 📋 異動店鋪（預計要排）")
    _dc1, _dc2 = st.columns([3, 2])
    with _dc1:
        la_date = st.date_input("日期", key="la_date")
    with _dc2:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        la_show_all = st.checkbox("顯示全部日期", key="la_show_all")

    l_src = fdf[fdf["_loc"] == "left"]
    if la_show_all:
        l_df = l_src
        st.caption(f"異動店鋪（**全部日期：{len(l_df)}**）")
    else:
        la_str = la_date.strftime("%Y-%m-%d")
        l_df   = l_src[_col_str(l_src["目前日期"]) == la_str]
        st.caption(f"異動店鋪（**{len(l_df)}**）")

    l_ed = st.data_editor(
        _edf_left(l_df),
        key=f"le_{ev}",
        use_container_width=True,
        hide_index=True,
        height=220,
        column_config=_CC_LEFT,
        disabled=_DIS_LEFT,
    )
    l_sel = _get_ids(l_ed, l_df)

    b_l1, b_l2 = st.columns(2)
    with b_l1:
        if st.button("⬇️ 移至現行班表", key="l2m", use_container_width=True):
            if _move_to_mid(l_sel, st.session_state.mb_date):
                st.rerun()
            else:
                st.toast("請先勾選店舖", icon="⚠️")
    with b_l2:
        if st.button("🗄️ 移至暫存區", key="l2r", use_container_width=True):
            if _move_to_right(l_sel):
                st.rerun()
            else:
                st.toast("請先勾選店舖", icon="⚠️")

    st.divider()

    # ── MIDDLE : 現行班表（匯入的班表）───────────────────────────────────────────
    st.markdown("### 📅 現行班表（匯入班表）")
    mb_date = st.date_input("日期", key="mb_date")

    mb_str = mb_date.strftime("%Y-%m-%d")
    m_src  = fdf[fdf["_loc"] == "middle"]
    m_df   = m_src[_col_str(m_src["目前日期"]) == mb_str]
    st.caption(f"現行班表（**{len(m_df)}**）")

    m_ed = st.data_editor(
        _edf_mid(m_df),
        key=f"me_{ev}",
        use_container_width=True,
        hide_index=True,
        height=220,
        column_config=_CC_MID,
        disabled=_DIS_MID,
    )
    m_sel = _get_ids(m_ed, m_df)

    b_m1, b_m2 = st.columns(2)
    with b_m1:
        if st.button("⬆️ 移回異動區", key="m2l", use_container_width=True):
            if _move_to_left(m_sel, st.session_state.la_date):
                st.rerun()
            else:
                st.toast("請先勾選店舖", icon="⚠️")
    with b_m2:
        if st.button("🗄️ 移至暫存區", key="m2r", use_container_width=True):
            if _move_to_right(m_sel):
                st.rerun()
            else:
                st.toast("請先勾選店舖", icon="⚠️")

    st.divider()

    # ── BOTTOM : 暫存區（暫存的資料）─────────────────────────────────────────────
    st.markdown("### 🗄️ 暫存區")

    r_df = fdf[fdf["_loc"] == "right"]
    st.caption(f"暫存店舖（**{len(r_df)}**）")

    r_c1, r_c2 = st.columns([2, 1])
    with r_c1:
        r_ed = st.data_editor(
            _edf_right(r_df),
            key=f"re_{ev}",
            use_container_width=True,
            hide_index=True,
            height=190,
            column_config=_CC_RIGHT,
            disabled=_DIS_RIGHT,
        )
        r_sel = _get_ids(r_ed, r_df)
    with r_c2:
        st.markdown("**指派控制**")
        tgt_date  = st.date_input("指派日期", key="tgt_date")
        tgt_shift = st.selectbox("指派班別", ["上午", "下午"], key="tgt_shift")
        if st.button("✅ 指派至現行班表", key="assign", use_container_width=True):
            if _assign_from_right(r_sel, tgt_date, tgt_shift):
                st.rerun()
            else:
                st.toast("請先勾選店舖", icon="⚠️")

# ═══ RIGHT : COMPARISON PANEL（隱藏區，預設收合）═════════════════════════════
with col_compare:
    st.markdown("### 📊 異動對照表")

    # Status summary metrics
    mc1, mc2 = st.columns(2)
    with mc1:
        st.metric("🟢 未變動", int((cdf["狀態"] == "🟢 未變動").sum()))
        st.metric("🔴 暫存中", int((cdf["狀態"] == "🔴 暫存中").sum()))
    with mc2:
        st.metric("🟡 已變更", int((cdf["狀態"] == "🟡 已變更").sum()))
        st.metric("🔵 新增",   int((cdf["狀態"] == "🔵 新增異動").sum()))

    chg_only = st.checkbox("📌 僅顯示變更項目", key="chg_only")

    tbl = pd.DataFrame({
        "店號":     cdf["店號"],
        "店名":     cdf["店名"],
        "狀態":     cdf["狀態"],
        "原本日期": cdf["原始日期"].apply(_fmt_date),
        "新日期":   cdf["目前日期"].apply(_fmt_date),
        "原本班別": cdf["原始班別"],
        "新班別":   cdf["目前班別"],
        "預定盤點者": cdf["預定盤點者"],
    }).reset_index(drop=True)

    if chg_only:
        tbl = tbl[tbl["狀態"] != "🟢 未變動"]

    _kw = st.session_state.get("g_kw", "").strip()
    _rg = st.session_state.get("g_rg", "全選")
    if _kw:
        tbl = tbl[
            tbl["店號"].str.contains(_kw, case=False, na=False) |
            tbl["店名"].str.contains(_kw, case=False, na=False)
        ]
    if _rg != "全選":
        tbl = tbl[tbl["店號"].isin(
            cdf[cdf["型態"] == _rg]["店號"]
        )]

    st.dataframe(
        tbl,
        use_container_width=True,
        hide_index=True,
        height=680,
        column_config={
            "狀態": st.column_config.TextColumn("狀態", width="small"),
        },
    )

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# EXPORT
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("## 📤 資料匯出")

exp = pd.DataFrame({
    "店號":       cdf["店號"],
    "店名":       cdf["店名"],
    "型態":       cdf["型態"],
    "原本日期":   cdf["原始日期"].apply(_fmt_date),
    "原本班別":   cdf["原始班別"],
    "狀態變更":   cdf["狀態"],
    "更動後日期": cdf["目前日期"].apply(_fmt_date),
    "更動後班別": cdf["目前班別"],
    "預定盤點者": cdf["預定盤點者"],
})

ec1, ec2 = st.columns(2)
with ec1:
    st.download_button(
        "📥 匯出 CSV",
        data=exp.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
        file_name=f"排班對照表_{date.today()}.csv",
        mime="text/csv",
        use_container_width=True,
    )
with ec2:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as wr:
        exp.to_excel(wr, index=False, sheet_name="排班對照表")
        ws = wr.sheets["排班對照表"]
        for col in ws.columns:
            wl = max((len(str(c.value)) if c.value else 0) for c in col)
            ws.column_dimensions[col[0].column_letter].width = max(wl + 2, 10)
    st.download_button(
        "📥 匯出 Excel (.xlsx)",
        data=buf.getvalue(),
        file_name=f"排班對照表_{date.today()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
