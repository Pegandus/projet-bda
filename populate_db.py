import mysql.connector
from faker import Faker
import random
import time

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'university_exams_db'
}

fake = Faker('fr_FR')

NB_DEPARTEMENTS = 7
NB_PROFS = 120
NB_FORMATIONS_PER_DEPT = 30
NB_MODULES_PER_FORMATION = 9
NB_ETUDIANTS = 14500
NB_SALLES = 60

def connect_db():
    return mysql.connector.connect(**DB_CONFIG)

def populate():
    conn = connect_db()
    cursor = conn.cursor()
    
    print("Demarrage de la generation des donnees...")
    start_time = time.time()

    print("Nettoyage de la base existante")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    tables = [
        'inscriptions', 'etudiants', 'modules', 'formations',
        'professeurs', 'lieux_examen', 'departements',
        'examens', 'surveillances'
    ]
    for t in tables:
        cursor.execute(f"TRUNCATE TABLE {t};")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    print("Base videe")

    print("Generation des departements")
    depts = [
        'Informatique', 'Mathematiques', 'Physique',
        'Chimie', 'Biologie', 'Genie Civil', 'Economie'
    ]
    for nom in depts:
        cursor.execute("INSERT INTO departements (nom) VALUES (%s)", (nom,))
    conn.commit()
    
    cursor.execute("SELECT id FROM departements")
    dept_ids = [row[0] for row in cursor.fetchall()]

    print("Generation des lieux")
    salles_data = []
    types = ['AMPHI', 'SALLE', 'LABO']
    for i in range(1, NB_SALLES + 1):
        t = random.choice(types)
        cap = 200 if t == 'AMPHI' else (20 if t == 'LABO' else random.choice([30, 40, 60]))
        nom = f"{t} {chr(65+i)}" if t == 'AMPHI' else f"Salle {100+i}"
        salles_data.append((nom, cap, t, 'Bloc A' if i < 15 else 'Bloc B'))
    cursor.executemany(
        "INSERT INTO lieux_examen (nom, capacite, type, batiment) VALUES (%s, %s, %s, %s)",
        salles_data
    )
    conn.commit()

    print("Generation des professeurs")
    profs_data = []
    for _ in range(NB_PROFS):
        nom = fake.last_name()
        prenom = fake.first_name()
        email = f"{prenom}.{nom}_{random.randint(1,9999)}@univ-exemple.dz".lower()
        dept = random.choice(dept_ids)
        specialite = fake.job()
        profs_data.append((nom, prenom, email, dept, specialite))
    cursor.executemany(
        "INSERT INTO professeurs (nom, prenom, email, dept_id, specialite) VALUES (%s, %s, %s, %s, %s)",
        profs_data
    )
    conn.commit()

    print("Generation des formations et modules")
    formations_ids = []
    modules_data = []
    niveaux = ['L1', 'L2', 'L3', 'M1', 'M2']
    
    for d_id in dept_ids:
        for i in range(NB_FORMATIONS_PER_DEPT):
            niv = niveaux[i % 5]
            nom_formation = f"Formation {niv} Dept {d_id}-{i}"
            cursor.execute(
                "INSERT INTO formations (nom, dept_id, niveau) VALUES (%s, %s, %s)",
                (nom_formation, d_id, niv)
            )
            f_id = cursor.lastrowid
            formations_ids.append(f_id)
            
            for m in range(NB_MODULES_PER_FORMATION):
                code = f"M{d_id}{f_id}{m}"
                nom_module = f"Module {code}"
                semestre = 1 if m < (NB_MODULES_PER_FORMATION / 2) else 2
                modules_data.append((nom_module, code, random.randint(2, 6), f_id, semestre))
    
    cursor.executemany(
        "INSERT INTO modules (nom, code_module, credits, formation_id, semestre) VALUES (%s, %s, %s, %s, %s)",
        modules_data
    )
    conn.commit()

    cursor.execute("SELECT id, formation_id FROM modules")
    all_modules = cursor.fetchall()
    modules_by_formation = {}
    for mid, fid in all_modules:
        modules_by_formation.setdefault(fid, []).append(mid)

    print(f"Generation de {NB_ETUDIANTS} etudiants")
    etudiants_data = []
    for i in range(NB_ETUDIANTS):
        nom = fake.last_name()
        prenom = fake.first_name()
        email = f"{prenom}.{nom}{i}@etu.univ.dz".lower()
        f_id = random.choice(formations_ids)
        promo = "2025-2026"
        etudiants_data.append((nom, prenom, email, f_id, promo))
    
    BATCH_SIZE = 2000
    for i in range(0, len(etudiants_data), BATCH_SIZE):
        batch = etudiants_data[i:i + BATCH_SIZE]
        cursor.executemany(
            "INSERT INTO etudiants (nom, prenom, email, formation_id, promo) VALUES (%s, %s, %s, %s, %s)",
            batch
        )
        conn.commit()
        print(f"{i + len(batch)} etudiants inseres")

    print("Generation des inscriptions")
    cursor.execute("SELECT id, formation_id FROM etudiants")
    real_students = cursor.fetchall()
    
    inscriptions_data = []
    for e_id, f_id in real_students:
        if f_id in modules_by_formation:
            for mod_id in modules_by_formation[f_id]:
                inscriptions_data.append((e_id, mod_id))
    
    print(f"{len(inscriptions_data)} inscriptions a creer")
    for i in range(0, len(inscriptions_data), BATCH_SIZE):
        batch = inscriptions_data[i:i + BATCH_SIZE]
        cursor.executemany(
            "INSERT INTO inscriptions (etudiant_id, module_id) VALUES (%s, %s)",
            batch
        )
        conn.commit()

    end_time = time.time()
    print(f"Succes total en {round(end_time - start_time, 2)} secondes")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    populate()
