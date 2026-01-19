import mysql.connector
from collections import defaultdict

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'university_exams_db'
}

def assign_surveillances():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    
    print("Assignation des surveillants...")

    query_exams = """
        SELECT e.id, e.date_examen, e.heure_debut, d.id as dept_id
        FROM examens e
        JOIN modules m ON e.module_id = m.id
        JOIN formations f ON m.formation_id = f.id
        JOIN departements d ON f.dept_id = d.id
        ORDER BY e.date_examen
    """
    cursor.execute(query_exams)
    exams = cursor.fetchall()

    cursor.execute("SELECT id, dept_id FROM professeurs")
    profs = cursor.fetchall()
    
    prof_load = {p['id']: 0 for p in profs}
    prof_schedule = defaultdict(set)
    
    profs_by_dept = defaultdict(list)
    for p in profs:
        profs_by_dept[p['dept_id']].append(p['id'])

    assignments = []
    
    for exam in exams:
        dept_id = exam['dept_id']
        date_heure = (exam['date_examen'], exam['heure_debut'])
        
        candidates = profs_by_dept[dept_id]
        candidates.sort(key=lambda pid: prof_load[pid])
        
        selected_prof = None
        for pid in candidates:
            if date_heure not in prof_schedule[pid]:
                selected_prof = pid
                break
        
        if selected_prof:
            assignments.append((exam['id'], selected_prof, 0))
            prof_load[selected_prof] += 1
            prof_schedule[selected_prof].add(date_heure)

    print(f"Enregistrement de {len(assignments)} surveillances...")
    cursor.execute("TRUNCATE TABLE surveillances")
    cursor.executemany(
        "INSERT INTO surveillances (examen_id, prof_id, est_responsable) VALUES (%s, %s, %s)",
        assignments
    )
    conn.commit()
    print("Professeurs assignés avec équité.")
    conn.close()

if __name__ == "__main__":
    assign_surveillances()
