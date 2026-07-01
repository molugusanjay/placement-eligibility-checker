import sqlite3
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

def init_db():
    print(f"Initializing database at: {DATABASE_PATH}")
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Create users table (handles auth and user roles)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('student', 'admin'))
    );
    ''')

    # Create students table (academic profiles)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        user_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        roll_no TEXT UNIQUE NOT NULL,
        branch TEXT NOT NULL,
        cgpa REAL NOT NULL,
        tenth_percent REAL NOT NULL,
        twelfth_percent REAL NOT NULL,
        active_backlogs INTEGER NOT NULL DEFAULT 0,
        history_backlogs INTEGER NOT NULL DEFAULT 0,
        graduation_year INTEGER NOT NULL,
        skills TEXT,
        resume_link TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    ''')

    # Create companies table (recruitment criteria)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        logo_color TEXT DEFAULT '#4f46e5',
        role TEXT NOT NULL,
        package TEXT NOT NULL,
        min_cgpa REAL NOT NULL DEFAULT 0.0,
        min_tenth REAL NOT NULL DEFAULT 0.0,
        min_twelfth REAL NOT NULL DEFAULT 0.0,
        max_backlogs INTEGER NOT NULL DEFAULT 0,
        allowed_branches TEXT NOT NULL DEFAULT 'All',
        deadline TEXT NOT NULL
    );
    ''')

    # Create applications table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        company_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'Applied' CHECK(status IN ('Applied', 'Shortlisted', 'Rejected', 'Selected')),
        cover_letter TEXT,
        preferred_location TEXT,
        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE,
        UNIQUE(student_id, company_id)
    );
    ''')

    conn.commit()

    # Seed initial data if tables are empty
    # Check if admin user exists
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    if cursor.fetchone()[0] == 0:
        print("Seeding initial data...")
        
        # 1. Insert Admins
        cursor.execute("INSERT INTO users (email, password, role) VALUES (?, ?, ?)", 
                       ('admin@tpo.com', 'admin123', 'admin'))
        
        # 2. Insert Students (Users first, then Profiles)
        students_data = [
            ('jane@student.com', 'student123', 'student', 'Jane Doe', 'CS045', 'Computer Science', 8.9, 92.5, 88.0, 0, 0, 2026, 'Python, JavaScript, SQL, React', 'https://resume.io/jane-doe'),
            ('john@student.com', 'student123', 'student', 'John Smith', 'ME102', 'Mechanical Eng', 7.2, 78.0, 72.5, 1, 2, 2026, 'AutoCAD, SolidWorks, Python', 'https://resume.io/john-smith'),
            ('sam@student.com', 'student123', 'student', 'Sam Wilson', 'EC088', 'Electronics Eng', 6.4, 65.0, 68.0, 0, 1, 2026, 'C++, Embedded Systems, IoT', 'https://resume.io/sam-wilson')
        ]
        
        for email, pwd, role, name, roll_no, branch, cgpa, tenth, twelfth, active_b, hist_b, grad_yr, skills, resume in students_data:
            cursor.execute("INSERT INTO users (email, password, role) VALUES (?, ?, ?)", (email, pwd, role))
            user_id = cursor.lastrowid
            cursor.execute('''
                INSERT INTO students (user_id, name, roll_no, branch, cgpa, tenth_percent, twelfth_percent, 
                                     active_backlogs, history_backlogs, graduation_year, skills, resume_link)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, name, roll_no, branch, cgpa, tenth, twelfth, active_b, hist_b, grad_yr, skills, resume))

        # 3. Insert Companies
        companies = [
            ('Google', '#ea4335', 'Software Engineer', '24 LPA', 8.5, 80.0, 80.0, 0, 'Computer Science, Electronics Eng', '2026-07-15'),
            ('Amazon', '#ff9900', 'Cloud Developer', '16 LPA', 8.0, 75.0, 75.0, 0, 'Computer Science, Electronics Eng', '2026-07-20'),
            ('Microsoft', '#00a4ef', 'System Engineer', '22 LPA', 8.5, 80.0, 80.0, 0, 'Computer Science, Electronics Eng', '2026-07-25'),
            ('Meta', '#0668e1', 'Frontend Engineer', '26 LPA', 9.0, 85.0, 85.0, 0, 'Computer Science', '2026-07-30'),
            ('Accenture', '#a100ff', 'Associate Architect', '4.5 LPA', 6.5, 60.0, 60.0, 1, 'All', '2026-08-05'),
            ('TCS Ninja', '#004b87', 'System Engineer', '3.6 LPA', 6.0, 60.0, 60.0, 2, 'All', '2026-08-10'),
            ('Wipro', '#4f2d7f', 'Project Engineer', '3.5 LPA', 6.0, 60.0, 60.0, 2, 'All', '2026-08-15'),
            ('Infosys', '#007cc3', 'Systems Associate', '3.6 LPA', 6.2, 60.0, 60.0, 1, 'All', '2026-08-20'),
            ('Cognizant', '#0033a0', 'Programmer Analyst', '4.0 LPA', 6.5, 60.0, 60.0, 1, 'Computer Science, Electronics Eng', '2026-08-25'),
            ('IBM', '#0f62fe', 'Technical Consultant', '7.5 LPA', 7.0, 70.0, 70.0, 0, 'Computer Science, Electronics Eng', '2026-08-30')
        ]
        
        for name, color, role, pkg, cgpa, tenth, twelfth, backlogs, branches, deadline in companies:
            cursor.execute('''
                INSERT INTO companies (name, logo_color, role, package, min_cgpa, min_tenth, min_twelfth, max_backlogs, allowed_branches, deadline)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, color, role, pkg, cgpa, tenth, twelfth, backlogs, branches, deadline))
            
        conn.commit()
        print("Initial database seeding completed successfully.")
    else:
        print("Database already populated. Skipping seed data.")

    conn.close()

if __name__ == '__main__':
    init_db()
