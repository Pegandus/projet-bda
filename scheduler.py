import mysql.connector
from datetime import date, timedelta
import time

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'university_exams_db'
}

DATE_DEBUT = date(2026, 1, 20)
CRENEAUX_HORAIRES = [
    ("08:30:00", "10:00:00"),
    ("10:30:00", "12:00:00"),
    ("13:00:00", "14:30:00"),
    ("15:00:00", "16:30:00")
]
DUREE = 90

def connect_db():
    return mysql.connector.connect(**DB_CONFIG)

def get_next_date(current_date):
    next_d = current_date + timedelta(days=1)
    while next_d.weekday() in [4, 5]:
        next_d += timedelta(days=1)
    return next_d

def scheduler():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    
    print("Demarrage de l'algorithme d'optimisation")
    start_time = time.time()

    print("Chargement des modules et effectifs")
    query_modules = """
        SELECT m.id, m.nom, m.formation_id, count(i.etudiant_id) as effectif 
        FROM modules m
        JOIN inscriptions i ON m.id = i.module_id
        GROUP BY m.id
        ORDER BY effectif DESC
    """
    cursor.execute(query_modules)
    modules_list = cursor.fetchall()

    print("Chargement des salles")
    cursor.execute(
        "SELECT id, nom, capacite FROM lieux_examen ORDER BY capacite ASC"
    )
    salles_list = cursor.fetchall()

    examens_prevus = []
    occupation_promo = {}
    occupation_salle = {}

    current_date = DATE_DEBUT
    occupation_promo[current_date] = {h[0]: set() for h in CRENEAUX_HORAIRES}
    occupation_salle[current_date] = {h[0]: set() for h in CRENEAUX_HORAIRES}

    unscheduled = []

    for mod in modules_list:
        placed = False
        effectif = mod['effectif']
        formation = mod['formation_id']
        test_date = current_date
        days_offset = 0

        while not placed and days_offset < 30:
            if test_date not in occupation_promo:
                occupation_promo[test_date] = {h[0]: set() for h in CRENEAUX_HORAIRES}
                occupation_salle[test_date] = {h[0]: set() for h in CRENEAUX_HORAIRES}

            for h_debut, h_fin in CRENEAUX_HORAIRES:
                if formation in occupation_promo[test_date][h_debut]:
                    continue
                
                salle_choisie = None
                for salle in salles_list:
                    if salle['capacite'] >= effectif:
                        if salle['id'] not in occupation_salle[test_date][h_debut]:
                            salle_choisie = salle
                            break
                
                if salle_choisie:
                    examens_prevus.append((
                        mod['id'], test_date, h_debut, h_fin,
                        DUREE, salle_choisie['id'], None
                    ))
                    
                    occupation_promo[test_date][h_debut].add(formation)
                    occupation_salle[test_date][h_debut].add(salle_choisie['id'])
                    placed = True
                    break

            if not placed:
                test_date = get_next_date(test_date)
                days_offset += 1

        if not placed:
            unscheduled.append(mod)

    print(f"Enregistrement de {len(examens_prevus)} examens")
    cursor.execute("SET FOREIGN_KEY_CHECKS=0")
    cursor.execute("TRUNCATE TABLE examens")
    cursor.execute("TRUNCATE TABLE surveillances")
    cursor.execute("SET FOREIGN_KEY_CHECKS=1")

    query_insert = """
        INSERT INTO examens
        (module_id, date_examen, heure_debut, heure_fin,
         duree_minutes, salle_id, responsable_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    cursor.executemany(query_insert, examens_prevus)
    conn.commit()

    end_time = time.time()
    duree_exec = round(end_time - start_time, 2)
    
    print(f"Termine en {duree_exec} secondes")
    print(f"{len(examens_prevus)} examens planifies, {len(unscheduled)} non planifies")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    scheduler()
