import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from src.utils.storage import load_all, MANUAL_DIR

st.set_page_config(
    page_title="Postgrados Chile",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Estilos ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.metric-card {
    background: #f0f4ff;
    border-radius: 12px;
    padding: 1rem 1.5rem;
    border-left: 4px solid #4361ee;
}
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    padding: 8px 20px;
}
</style>
""", unsafe_allow_html=True)

# ── Carga de datos ────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def cargar():
    df = load_all()
    if df.empty:
        return df
    if "arancel_clp" in df.columns:
        df["arancel_clp"] = pd.to_numeric(df["arancel_clp"], errors="coerce")
    for col in ["tipo", "area", "modalidad", "institucion"]:
        if col in df.columns:
            df[col] = df[col].fillna("Sin datos").str.strip()
    return df

df_full = cargar()

# ── Sidebar: Filtros ──────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Flag_of_Chile.svg/200px-Flag_of_Chile.svg.png", width=60)
    st.title("🎓 Postgrados Chile")
    st.caption("Análisis del mercado de educación continua")
    st.divider()

    if df_full.empty:
        st.warning("Sin datos. Ingesta un CSV primero.")
        filtros_activos = False
    else:
        st.subheader("Filtros")
        tipos = ["Todos"] + sorted(df_full["tipo"].unique().tolist()) if "tipo" in df_full.columns else ["Todos"]
        modalidades = ["Todas"] + sorted(df_full["modalidad"].unique().tolist()) if "modalidad" in df_full.columns else ["Todas"]
        areas = ["Todas"] + sorted(df_full["area"].unique().tolist()) if "area" in df_full.columns else ["Todas"]
        instituciones = ["Todas"] + sorted(df_full["institucion"].unique().tolist()) if "institucion" in df_full.columns else ["Todas"]

        sel_tipo = st.selectbox("Tipo de programa", tipos)
        sel_modalidad = st.selectbox("Modalidad", modalidades)
        sel_area = st.selectbox("Área", areas)
        sel_inst = st.selectbox("Institución", instituciones)

        precio_max = None
        if "arancel_clp" in df_full.columns:
            precio_vals = df_full["arancel_clp"].dropna()
            if not precio_vals.empty:
                precio_max_val = int(precio_vals.max())
                precio_min_val = int(precio_vals.min())
                rango = st.slider(
                    "Arancel CLP",
                    min_value=precio_min_val,
                    max_value=precio_max_val,
                    value=(precio_min_val, precio_max_val),
                    step=100_000,
                    format="$%d",
                )
                precio_max = rango

        filtros_activos = True

    st.divider()
    st.caption("Fuentes: UC · UChile · USACH · UAI · CNED · Manual")

# ── Aplicar filtros ───────────────────────────────────────────────────────────
if not df_full.empty and filtros_activos:
    df = df_full.copy()
    if sel_tipo != "Todos":
        df = df[df["tipo"] == sel_tipo]
    if sel_modalidad != "Todas":
        df = df[df["modalidad"] == sel_modalidad]
    if sel_area != "Todas":
        df = df[df["area"] == sel_area]
    if sel_inst != "Todas":
        df = df[df["institucion"] == sel_inst]
    if precio_max and "arancel_clp" in df.columns:
        df = df[(df["arancel_clp"].isna()) | ((df["arancel_clp"] >= precio_max[0]) & (df["arancel_clp"] <= precio_max[1]))]
else:
    df = df_full.copy()

# ── Ingesta rápida desde sidebar ──────────────────────────────────────────────
with st.sidebar:
    st.subheader("📥 Agregar datos")
    uploaded = st.file_uploader("Subir CSV", type="csv", help="Columnas: institucion, nombre, tipo, area, modalidad")
    if uploaded:
        try:
            df_up = pd.read_csv(uploaded)
            required = {"institucion", "nombre", "tipo", "area", "modalidad"}
            missing = required - set(df_up.columns)
            if missing:
                st.error(f"Faltan columnas: {missing}")
            else:
                dest = MANUAL_DIR / "programas.csv"
                if dest.exists():
                    existing = pd.read_csv(dest)
                    df_up = pd.concat([existing, df_up], ignore_index=True).drop_duplicates(
                        subset=["institucion", "nombre", "tipo"]
                    )
                df_up.to_csv(dest, index=False)
                st.success(f"✅ {len(df_up)} programas guardados")
                st.cache_data.clear()
                st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# CONTENIDO PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

if df_full.empty:
    st.title("🎓 Mercado de Postgrados Chile")
    st.info("No hay datos cargados aún. Sube un CSV desde el panel izquierdo o corre `python -m src.cli ingestar data/manual/programas_ejemplo.csv` en la terminal.")
    st.stop()

# ── KPIs ──────────────────────────────────────────────────────────────────────
st.title("🎓 Mercado de Postgrados Chile")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Programas", len(df), delta=f"{len(df_full)-len(df):+d}" if len(df) != len(df_full) else None)
with col2:
    st.metric("Instituciones", df["institucion"].nunique() if "institucion" in df.columns else "-")
with col3:
    online_pct = round(df[df["modalidad"].isin(["online","hibrido"])].shape[0] / max(len(df),1) * 100) if "modalidad" in df.columns else 0
    st.metric("Online / Híbrido", f"{online_pct}%")
with col4:
    precios = df["arancel_clp"].dropna() if "arancel_clp" in df.columns else pd.Series(dtype=float)
    st.metric("Precio mediano", f"${precios.median()/1e6:.1f}M" if not precios.empty else "N/D")
with col5:
    st.metric("Áreas", df["area"].nunique() if "area" in df.columns else "-")

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Oferta", "💰 Precios", "🌐 Modalidad", "🏛 Instituciones", "📋 Datos"])

# ────────────────────────────────────────────────────────────────────────────
# TAB 1: Oferta
# ────────────────────────────────────────────────────────────────────────────
with tab1:
    c1, c2 = st.columns(2)

    with c1:
        if "tipo" in df.columns:
            conteo_tipo = df["tipo"].value_counts().reset_index()
            conteo_tipo.columns = ["Tipo", "Cantidad"]
            fig = px.pie(conteo_tipo, names="Tipo", values="Cantidad",
                         title="Distribución por tipo de programa",
                         color_discrete_sequence=px.colors.qualitative.Set2,
                         hole=0.4)
            fig.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        if "area" in df.columns:
            conteo_area = df["area"].value_counts().reset_index()
            conteo_area.columns = ["Área", "Cantidad"]
            fig2 = px.bar(conteo_area, x="Cantidad", y="Área", orientation="h",
                          title="Programas por área del conocimiento",
                          color="Cantidad",
                          color_continuous_scale="Blues")
            fig2.update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False)
            st.plotly_chart(fig2, use_container_width=True)

    if "tipo" in df.columns and "area" in df.columns:
        pivot = df.groupby(["area", "tipo"]).size().reset_index(name="n")
        fig3 = px.bar(pivot, x="area", y="n", color="tipo",
                      title="Oferta por área y tipo de programa",
                      barmode="stack",
                      color_discrete_sequence=px.colors.qualitative.Pastel)
        fig3.update_layout(xaxis_title="Área", yaxis_title="Cantidad")
        st.plotly_chart(fig3, use_container_width=True)

# ────────────────────────────────────────────────────────────────────────────
# TAB 2: Precios
# ────────────────────────────────────────────────────────────────────────────
with tab2:
    precios_df = df[df["arancel_clp"].notna() & (df["arancel_clp"] > 0)].copy() if "arancel_clp" in df.columns else pd.DataFrame()

    if precios_df.empty:
        st.info("No hay datos de precios en la selección actual.")
    else:
        c1, c2 = st.columns(2)

        with c1:
            fig = px.box(precios_df, x="tipo", y="arancel_clp",
                         title="Distribución de precios por tipo",
                         color="tipo",
                         color_discrete_sequence=px.colors.qualitative.Set1)
            fig.update_layout(yaxis_title="Arancel CLP", xaxis_title="", showlegend=False)
            fig.update_yaxes(tickformat="$,.0f")
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            if "modalidad" in precios_df.columns:
                fig2 = px.violin(precios_df, x="modalidad", y="arancel_clp",
                                 title="Precios según modalidad",
                                 color="modalidad",
                                 box=True,
                                 color_discrete_sequence=px.colors.qualitative.Pastel1)
                fig2.update_layout(yaxis_title="Arancel CLP", xaxis_title="", showlegend=False)
                fig2.update_yaxes(tickformat="$,.0f")
                st.plotly_chart(fig2, use_container_width=True)

        st.subheader("Estadísticas de precios por tipo")
        stats = precios_df.groupby("tipo")["arancel_clp"].agg(
            Promedio="mean", Mediana="median", Mínimo="min", Máximo="max", N="count"
        ).reset_index()
        for col in ["Promedio", "Mediana", "Mínimo", "Máximo"]:
            stats[col] = stats[col].apply(lambda x: f"${x:,.0f}")
        st.dataframe(stats, use_container_width=True, hide_index=True)

        st.subheader("Top 10 programas más caros")
        top = precios_df.nlargest(10, "arancel_clp")[["nombre", "institucion", "tipo", "modalidad", "arancel_clp"]]
        top["arancel_clp"] = top["arancel_clp"].apply(lambda x: f"${x:,.0f}")
        st.dataframe(top, use_container_width=True, hide_index=True)

# ────────────────────────────────────────────────────────────────────────────
# TAB 3: Modalidad
# ────────────────────────────────────────────────────────────────────────────
with tab3:
    if "modalidad" not in df.columns:
        st.info("Sin datos de modalidad.")
    else:
        c1, c2 = st.columns(2)

        with c1:
            modal_count = df["modalidad"].value_counts().reset_index()
            modal_count.columns = ["Modalidad", "Cantidad"]
            colors = {"presencial": "#4361ee", "online": "#7209b7", "hibrido": "#f72585"}
            fig = px.pie(modal_count, names="Modalidad", values="Cantidad",
                         title="Distribución por modalidad",
                         color="Modalidad",
                         color_discrete_map=colors,
                         hole=0.5)
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            if "tipo" in df.columns:
                modal_tipo = df.groupby(["modalidad", "tipo"]).size().reset_index(name="n")
                fig2 = px.bar(modal_tipo, x="modalidad", y="n", color="tipo",
                              title="Modalidad × Tipo de programa",
                              barmode="group",
                              color_discrete_sequence=px.colors.qualitative.Set2)
                st.plotly_chart(fig2, use_container_width=True)

        if "institucion" in df.columns:
            st.subheader("Instituciones con mayor oferta online/híbrida")
            online_inst = df[df["modalidad"].isin(["online", "hibrido"])].groupby("institucion").size().reset_index(name="Programas online+híbrido")
            online_inst = online_inst.sort_values("Programas online+híbrido", ascending=False).head(15)
            fig3 = px.bar(online_inst, x="Programas online+híbrido", y="institucion",
                          orientation="h",
                          color="Programas online+híbrido",
                          color_continuous_scale="Purples")
            fig3.update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False)
            st.plotly_chart(fig3, use_container_width=True)

# ────────────────────────────────────────────────────────────────────────────
# TAB 4: Instituciones
# ────────────────────────────────────────────────────────────────────────────
with tab4:
    if "institucion" not in df.columns:
        st.info("Sin datos de institución.")
    else:
        inst_df = df.groupby("institucion").agg(
            Total=("nombre", "count"),
            Magisteres=("tipo", lambda s: (s == "magister").sum()),
            Doctorados=("tipo", lambda s: (s == "doctorado").sum()),
            Diplomados=("tipo", lambda s: (s == "diplomado").sum()),
            Online=("modalidad", lambda s: s.isin(["online","hibrido"]).sum()),
        ).reset_index().sort_values("Total", ascending=False)

        c1, c2 = st.columns([3, 2])
        with c1:
            fig = px.bar(inst_df.head(15), x="Total", y="institucion",
                         orientation="h",
                         title="Top instituciones por número de programas",
                         color="Total", color_continuous_scale="Blues")
            fig.update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            fig2 = px.scatter(inst_df, x="Magisteres", y="Doctorados",
                              size="Total", color="Online",
                              hover_name="institucion",
                              title="Magisteres vs Doctorados (tamaño=total, color=online)",
                              color_continuous_scale="Viridis")
            st.plotly_chart(fig2, use_container_width=True)

        st.dataframe(inst_df, use_container_width=True, hide_index=True)

# ────────────────────────────────────────────────────────────────────────────
# TAB 5: Datos brutos
# ────────────────────────────────────────────────────────────────────────────
with tab5:
    st.subheader(f"Tabla de datos ({len(df)} programas)")

    busqueda = st.text_input("🔍 Buscar en nombre o institución", placeholder="ej: magíster, derecho, UC...")
    if busqueda:
        mask = df["nombre"].str.contains(busqueda, case=False, na=False)
        if "institucion" in df.columns:
            mask |= df["institucion"].str.contains(busqueda, case=False, na=False)
        df_show = df[mask]
    else:
        df_show = df

    cols_mostrar = [c for c in ["nombre", "institucion", "tipo", "area", "modalidad", "arancel_clp", "duracion_meses", "ciudad", "url"] if c in df_show.columns]
    st.dataframe(df_show[cols_mostrar], use_container_width=True, hide_index=True)

    csv = df_show[cols_mostrar].to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Descargar CSV", csv, "programas_filtrados.csv", "text/csv")
