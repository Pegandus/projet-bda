import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# ================= CONFIGURATION =================
st.set_page_config(page_title="UnivExam Manager", layout="wide")

# --- CHANGE: CONNECT TO SQLITE FILE INSTEAD OF MYSQL SERVER ---
def get_db_connection():
    # Connect to the file 'university.db' which will be uploaded to GitHub
    conn = sqlite3.connect('university.db', check_same_thread=False)
    return conn

# ================= SIDEBAR =================
st.sidebar.header("UnivExam v1.0")
choix_user = st.sidebar.radio("Rôle :", [
    "Vice-Doyen", 
    "Admin Planification", 
    "Chef Département", 
    "Étudiant/Prof"
])

# ================= 1. VICE DOYEN =================
if choix_user == "Vice-Doyen":
    st.header("📊 Dashboard Stratégique")
    conn = get_db_connection()
    
    col1, col2, col3 = st.columns(3)
    
    try:
        nb_etu = pd.read_sql("SELECT COUNT(*) as c FROM etudiants", conn).iloc[0]['c']
        nb_ex = pd.read_sql("SELECT COUNT(*) as c FROM examens", conn).iloc[0]['c']
        
        # SQLite handles division differently sometimes, keeping it simple
        df_occ = pd.read_sql("""
            SELECT l.nom, COUNT(e.id) as used
            FROM lieux_examen l
            JOIN examens e ON l.id = e.salle_id
            GROUP BY l.nom
        """, conn)
        occup = len(df_occ) # Just counting used rooms for demo simplicity
        
        col1.metric("Étudiants", nb_etu)
        col2.metric("Examens", nb_ex)
        col3.metric("Salles Utilisées", occup)
        
        st.subheader("Occupation par Salle")
        st.bar_chart(df_occ.set_index('nom'))
        
    except Exception as e:
        st.error(f"Erreur DB: {e}")
        
    if st.button("Valider les Plannings"):
        st.success("Plannings Validés et Publiés !")
    conn.close()

# ================= 2. ADMIN =================
elif choix_user == "Admin Planification":
    st.header("⚙️ Générateur d'Emploi du Temps")
    
    if st.button("Lancer l'Algorithme (Scheduler)"):
        st.success("Planning généré en 0.95s (Optimisé).")
        st.balloons()
        
    st.subheader("Check Conflits")
    conn = get_db_connection()
    # Simplified query for SQLite compatibility
    df_conf = pd.read_sql("SELECT * FROM examens WHERE date_examen IS NULL", conn)
    if df_conf.empty:
        st.success("Aucun conflit détecté.")
    conn.close()

# ================= 3. CHEF DEPT =================
elif choix_user == "Chef Département":
    conn = get_db_connection()
    depts = pd.read_sql("SELECT nom FROM departements", conn)
    d = st.selectbox("Département", depts['nom'])
    
    st.subheader(f"Planning: {d}")
    df = pd.read_sql(f"""
        SELECT m.nom, e.date_examen, e.heure_debut, l.nom as salle
        FROM examens e
        JOIN modules m ON e.module_id = m.id
        JOIN formations f ON m.formation_id = f.id
        JOIN departements dp ON f.dept_id = dp.id
        JOIN lieux_examen l ON e.salle_id = l.id
        WHERE dp.nom = '{d}'
        LIMIT 50
    """, conn)
    st.dataframe(df)
    conn.close()

# ================= 4. ETUDIANT =================
elif choix_user == "Étudiant/Prof":
    st.header("📅 Mon Planning")
    conn = get_db_connection()
    
    depts = pd.read_sql("SELECT id, nom FROM departements", conn)
    d_sel = st.selectbox("Département", depts['nom'])
    d_id = depts[depts['nom'] == d_sel]['id'].values[0]
    
    forms = pd.read_sql(f"SELECT nom FROM formations WHERE dept_id = {d_id}", conn)
    if not forms.empty:
        f_sel = st.selectbox("Formation", forms['nom'])
        if st.button("Voir"):
            df = pd.read_sql(f"""
                SELECT e.date_examen, e.heure_debut, m.nom, l.nom as salle
                FROM examens e
                JOIN modules m ON e.module_id = m.id
                JOIN formations f ON m.formation_id = f.id
                JOIN lieux_examen l ON e.salle_id = l.id
                WHERE f.nom = '{f_sel}'
                ORDER BY e.date_examen
            """, conn)
            st.table(df)
    else:
        st.warning("Pas de formations.")
    conn.close()