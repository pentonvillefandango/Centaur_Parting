from centaur.db.session import init_db

if __name__ == "__main__":
    print("Initializing Centaur Parting database...")
    init_db()
    print("Done. Database created as cp_data.db")

