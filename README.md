# PrepEligible // Placement Eligibility Checker Portal

PrepEligible is a responsive full-stack web application designed for academic placement cells and training/placement offices (TPO). It automatically checks and displays a student's eligibility for recruitment drives in real-time by evaluating academic details against customizable company requirements.

---

##  Key Features

### For Students
- **Real-Time Eligibility Engine**: Automatically checks CGPA, 10th & 12th marks, active backlogs, and branch eligibility against all visiting companies.
- **Academic Profile Editor**: Update academic statistics, resumes, and lists of skills instantly.
- **Eligibility Checklist**: Visual drawer detailing exactly which criteria passed or failed for a specific job posting.
- **Application Tracking**: Submit applications to eligible companies and monitor recruitment status (Applied, Shortlisted, Selected, Rejected).

### For Training & Placement Officers (TPO / Admin)
- **Analytics Dashboard**: Performance metrics including average CGPA, job post counts, application counts, and student placement rates.
- **Student Registry**: Interactive database containing details of all registered students with instant search and branch filters.
- **Criteria & Job Posting Manager**: Create and delete job opportunities. Define minimum CGPA, backlog limits, allowed departments, packages, deadlines, and UI branding colors.
- **Application Review Panel**: Review student profiles, inspect resumes, and update application statuses (Shortlist, Select, Reject).

---

## 🛠️ Technology Stack
- **Backend API**: Python 3.14+ / Flask 3.1
- **Database**: SQLite3 (File-based, zero configuration)
- **Frontend SPA**: Vanilla HTML5, modern CSS3 (featuring responsive grids and dark glassmorphic design), and Javascript (ES6+ fetch client & router).

---

## 📂 Project Architecture & Directory Structure

```text
placement-eligibility-checker/
│
├── database.db             # SQLite database file (created automatically on startup)
├── db_init.py              # Database schema builder and seed data generator
├── app.py                  # Main Flask web application (REST API and routing)
├── run.py                  # Startup script (verifies database, runs server, opens browser)
│
└── static/                 # Static asset folder served by Flask
    ├── index.html          # Main Single Page Application UI structure
    │
    ├── css/
    │   └── style.css       # Custom glassmorphic styling, variables, and responsive layout
    │
    └── js/
        └── app.js          # Controller handles auth, SPA routing, API fetch, UI rendering
```

---

## ⚙️ Running the Application

### Prerequisites
You only need **Python 3** and **Flask** installed on your system. 

1. **Verify Python is installed**:
   ```bash
   python --version
   ```
2. **Install Flask** (if you don't have it installed):
   ```bash
   pip install Flask
   ```

### Quick Start
To launch the application, initialize the database automatically, and open the web portal, run the startup script:

```powershell
python run.py
```

The portal will open in your default browser at **`http://127.0.0.1:5000`**.

---

## 🔑 Test Credentials

You can use the following seeded user profiles to test and demonstrate all features of the portal:

### 1. Training & Placement Officer (TPO Admin View)
- **Email**: `admin@tpo.com`
- **Password**: `admin123`

### 2. Eligible Student Profile
- **Email**: `jane@student.com`
- **Password**: `student123`
- *Profile Details*: CGPA 8.9, 0 Backlogs, Computer Science. (Eligible for all companies)

### 3. Student with Backlogs (Ineligible for some companies)
- **Email**: `john@student.com`
- **Password**: `student123`
- *Profile Details*: CGPA 7.2, 1 Active Backlog, Mechanical Engineering. (Ineligible for Google due to backlogs and branch)

---

## 🧠 Core Eligibility Algorithm
The system checks eligibility using the following backend constraints (`app.py`):

1. **CGPA Criterion**: `Student CGPA >= Company Minimum CGPA`
2. **10th Grade Score**: `Student 10th % >= Company Minimum 10th %`
3. **12th Grade Score**: `Student 12th % >= Company Minimum 12th %`
4. **Active Backlogs**: `Student Active Backlogs <= Company Maximum Backlogs Allowed`
5. **Specialization**: `Company Allowed Branches == 'All'` OR `Student Branch` is listed in the company's allowed branches list (case-insensitive check).
