
import streamlit as st
import pandas as pd
import plotly.express as px
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import xml.etree.ElementTree as ET
from io import BytesIO

st.set_page_config(layout="wide", page_title="Jumeau Numérique LGV V6")

st.title("🧠 Jumeau Numérique LGV – V6 Clé en Main")

# Charger les données
df_postes = pd.read_csv("postes_lgv_simulés.csv")
df_gantt = pd.read_csv("gantt_data.csv")
df_gantt["Début"] = pd.to_datetime(df_gantt["Début"])
df_gantt["Fin"] = pd.to_datetime(df_gantt["Fin"])

# Menu
st.sidebar.title("📍 Navigation")
page = st.sidebar.radio("Aller à :", ["Carte", "Tableau de bord", "Planning Gantt", "BIM Viewer", "Export MS Project"])

# 📍 Carte interactive
if page == "Carte":
    st.header("🗺️ Carte interactive des postes")
    df_map = df_postes.rename(columns={"Latitude": "lat", "Longitude": "lon"})
    st.map(df_map, zoom=6)
    st.dataframe(df_postes)

# 📊 Tableau de bord par étape
elif page == "Tableau de bord":
    st.header("📊 Suivi global par étape")
    etapes = ["GC", "Bâtiment", "MALT", "HT", "BT", "CC", "ESSAIS"]
    for etape in etapes:
        st.subheader(f"Étape : {etape}")
        st.write(df_postes[["Nom", "Type", "PK", etape]][df_postes[etape] != "Non démarré"])

# 📅 Gantt interactif avec édition
elif page == "Planning Gantt":
    st.header("📅 Planning Gantt interactif")
    # Filtres
    postes = st.multiselect("Postes", df_gantt["Poste"].unique(), default=df_gantt["Poste"].unique())
    etapes = st.multiselect("Étapes", df_gantt["Étape"].unique(), default=df_gantt["Étape"].unique())
    types = st.multiselect("Types", df_gantt["Type"].unique(), default=df_gantt["Type"].unique())
    df_filtered = df_gantt[df_gantt["Poste"].isin(postes) & df_gantt["Étape"].isin(etapes) & df_gantt["Type"].isin(types)]

    # Zoom temporel
    date_min = st.date_input("Date début", df_filtered["Début"].min().date())
    date_max = st.date_input("Date fin", df_filtered["Fin"].max().date())
    df_filtered = df_filtered[(df_filtered["Début"] >= pd.to_datetime(date_min)) & (df_filtered["Début"] <= pd.to_datetime(date_max))]

    # Gantt
    fig = px.timeline(df_filtered, x_start="Début", x_end="Fin", y="Poste", color="Étape", title="Planning")
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)

    # Table éditable
    st.subheader("✏️ Modifier le planning")
    gb = GridOptionsBuilder.from_dataframe(df_gantt)
    gb.configure_default_column(editable=True)
    gridoptions = gb.build()
    grid_table = AgGrid(df_gantt, gridOptions=gridoptions, update_mode=GridUpdateMode.MANUAL, height=400)

    if st.button("💾 Sauvegarder"):
        new_df = grid_table["data"]
        pd.DataFrame(new_df).to_csv("gantt_data.csv", index=False)
        st.success("Modifications enregistrées.")

# 🏗️ BIM Viewer
elif page == "BIM Viewer":
    st.header("🏗️ Visionneuse BIM intégrée")
    st.markdown("Ci-dessous un exemple de visionneuse IFC.js")
    st.components.v1.iframe("https://ifcjs.github.io/hello-world/", height=600)

# 📤 Export MS Project (.xml)
elif page == "Export MS Project":
    st.header("📤 Exporter vers MS Project (XML)")
    def export_xml(df):
        project = ET.Element("Project")
        tasks = ET.SubElement(project, "Tasks")
        for i, row in df.iterrows():
            task = ET.SubElement(tasks, "Task")
            ET.SubElement(task, "UID").text = str(i + 1)
            ET.SubElement(task, "ID").text = str(i + 1)
            ET.SubElement(task, "Name").text = f"{row['Poste']} - {row['Étape']}"
            ET.SubElement(task, "Start").text = pd.to_datetime(row["Début"]).strftime("%Y-%m-%dT08:00:00")
            ET.SubElement(task, "Finish").text = pd.to_datetime(row["Fin"]).strftime("%Y-%m-%dT17:00:00")
            ET.SubElement(task, "Duration").text = f"PT{(pd.to_datetime(row['Fin']) - pd.to_datetime(row['Début'])).days * 8}H0M0S"
            ET.SubElement(task, "Manual").text = "1"
        tree = ET.ElementTree(project)
        buffer = BytesIO()
        tree.write(buffer, encoding="utf-8", xml_declaration=True)
        buffer.seek(0)
        return buffer

    if st.button("📥 Générer fichier XML"):
        xml_file = export_xml(df_gantt)
        st.download_button("Télécharger le fichier MS Project", xml_file, file_name="lgv_project.xml")
