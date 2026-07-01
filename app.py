from flask import Flask, request, jsonify, session, send_from_directory
import sqlite3
import os
from datetime import datetime
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='static', static_url_path='')
app.secret_key = 'tpo_secret_placement_checker_key_2026'

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

# --- Upload Configuration ---
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- SMTP Configuration (reads from environment variables) ---
SMTP_HOST = os.environ.get('SMTP_HOST', '')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASS = os.environ.get('SMTP_PASS', '')

# --- Email Logger (separate from Flask logs) ---
EMAIL_LOG_PATH = os.path.join(os.path.dirname(__file__), 'emails_sent.log')
email_logger = logging.getLogger('email_notifications')
email_logger.setLevel(logging.INFO)
email_handler = logging.FileHandler(EMAIL_LOG_PATH)
email_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
email_logger.addHandler(email_handler)


def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def allowed_file(filename):
    """Check that an uploaded file has a .pdf extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def send_eligibility_email(student, company):
    """
    Sends an HTML email to a student about a new eligible opportunity.
    Falls back to log file if SMTP is not configured or fails.
    """
    subject = f"New Opportunity: {company['name']} — {company['role']}"

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background: #f4f4f4; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background: white; border-radius: 8px; padding: 30px;">
            <h2 style="color: #4f46e5;">New Placement Opportunity!</h2>
            <p>Hi <strong>{student['name']}</strong>,</p>
            <p>A new company has been posted on the TPO Portal and you are <strong style="color: green;">eligible</strong> to apply!</p>
            <table style="width:100%; border-collapse:collapse; margin: 20px 0;">
                <tr style="background:#f0f0ff;">
                    <td style="padding:10px; font-weight:bold;">Company</td>
                    <td style="padding:10px;">{company['name']}</td>
                </tr>
                <tr>
                    <td style="padding:10px; font-weight:bold;">Role</td>
                    <td style="padding:10px;">{company['role']}</td>
                </tr>
                <tr style="background:#f0f0ff;">
                    <td style="padding:10px; font-weight:bold;">Package</td>
                    <td style="padding:10px;">{company['package']}</td>
                </tr>
                <tr>
                    <td style="padding:10px; font-weight:bold;">Deadline</td>
                    <td style="padding:10px;">{company['deadline']}</td>
                </tr>
            </table>
            <p>Log in to the portal to apply before the deadline!</p>
            <p style="color: #888; font-size: 12px;">— TPO Placement Cell</p>
        </div>
    </body>
    </html>
    """

    log_message = (
        f"EMAIL TO: {student['email']} | "
        f"STUDENT: {student['name']} (CGPA: {student['cgpa']}) | "
        f"COMPANY: {company['name']} - {company['role']} | "
        f"PACKAGE: {company['package']} | DEADLINE: {company['deadline']}"
    )

    if SMTP_HOST and SMTP_USER and SMTP_PASS:
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = SMTP_USER
            msg['To'] = student['email']
            msg.attach(MIMEText(html_body, 'html'))

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.ehlo()
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(SMTP_USER, student['email'], msg.as_string())

            email_logger.info(f"SENT (SMTP) | {log_message}")
            print(f"[EMAIL SENT] To: {student['email']} for {company['name']}")
        except Exception as e:
            email_logger.info(f"LOGGED (SMTP failed: {e}) | {log_message}")
            print(f"[EMAIL LOGGED] SMTP error: {e}. Logged to emails_sent.log")
    else:
        email_logger.info(f"LOGGED (no SMTP config) | {log_message}")
        print(f"[EMAIL LOGGED] No SMTP configured. Logged to emails_sent.log")


# Helper: Check eligibility details
def evaluate_eligibility(student, company):
    eligible = True
    reasons = []

    # 1. CGPA check
    if student['cgpa'] < company['min_cgpa']:
        eligible = False
        reasons.append(f"CGPA is {student['cgpa']:.2f}, required is {company['min_cgpa']:.2f}")

    # 2. 10th Grade Percent check
    if student['tenth_percent'] < company['min_tenth']:
        eligible = False
        reasons.append(f"10th marks are {student['tenth_percent']:.1f}%, required is {company['min_tenth']:.1f}%")

    # 3. 12th Grade Percent check
    if student['twelfth_percent'] < company['min_twelfth']:
        eligible = False
        reasons.append(f"12th marks are {student['twelfth_percent']:.1f}%, required is {company['min_twelfth']:.1f}%")

    # 4. Backlog check
    if student['active_backlogs'] > company['max_backlogs']:
        eligible = False
        reasons.append(f"Active backlogs count is {student['active_backlogs']}, max allowed is {company['max_backlogs']}")

    # 5. Branch eligibility check
    allowed_branches_str = company['allowed_branches']
    if allowed_branches_str.lower() != 'all':
        allowed_branches = [b.strip().lower() for b in allowed_branches_str.split(',')]
        student_branch = student['branch'].strip().lower()
        if student_branch not in allowed_branches:
            eligible = False
            reasons.append(f"Branch '{student['branch']}' is not in allowed list: {company['allowed_branches']}")

    return {
        "eligible": eligible,
        "reasons": reasons
    }


# ----------------- Static File Routes -----------------
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


# ----------------- Auth API Endpoints -----------------
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    required_fields = ['email', 'password', 'name', 'roll_no', 'branch', 'cgpa', 'tenth_percent', 'twelfth_percent', 'graduation_year']
    for field in required_fields:
        if field not in data or data[field] == '':
            return jsonify({"error": f"Field '{field}' is required"}), 400

    email = data['email']
    password = data['password']
    name = data['name']
    roll_no = data['roll_no']
    branch = data['branch']
    try:
        cgpa = float(data['cgpa'])
        tenth_percent = float(data['tenth_percent'])
        twelfth_percent = float(data['twelfth_percent'])
        active_backlogs = int(data.get('active_backlogs', 0))
        history_backlogs = int(data.get('history_backlogs', 0))
        graduation_year = int(data['graduation_year'])
    except ValueError:
        return jsonify({"error": "Numeric values are invalid"}), 400

    skills = data.get('skills', '')
    resume_link = data.get('resume_link', '')

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO users (email, password, role) VALUES (?, ?, 'student')", (email, password))
        user_id = cursor.lastrowid

        cursor.execute('''
            INSERT INTO students (user_id, name, roll_no, branch, cgpa, tenth_percent, twelfth_percent, 
                                 active_backlogs, history_backlogs, graduation_year, skills, resume_link)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, name, roll_no, branch, cgpa, tenth_percent, twelfth_percent,
              active_backlogs, history_backlogs, graduation_year, skills, resume_link))

        conn.commit()
        return jsonify({"success": True, "message": "Student registered successfully"}), 201
    except sqlite3.IntegrityError as e:
        conn.rollback()
        if "users.email" in str(e) or "email" in str(e):
            return jsonify({"error": "Email address already registered"}), 400
        if "students.roll_no" in str(e) or "roll_no" in str(e):
            return jsonify({"error": "Roll Number already exists"}), 400
        return jsonify({"error": f"Integrity error: {str(e)}"}), 400
    finally:
        conn.close()


@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({"error": "Email and password are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (data['email'], data['password']))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({"error": "Invalid email or password"}), 401

    session['user_id'] = user['id']
    session['role'] = user['role']

    user_details = {
        "id": user['id'],
        "email": user['email'],
        "role": user['role'],
        "name": user['email'].split('@')[0].capitalize()
    }

    if user['role'] == 'student':
        cursor.execute("SELECT name FROM students WHERE user_id = ?", (user['id'],))
        student_prof = cursor.fetchone()
        if student_prof:
            user_details['name'] = student_prof['name']

    conn.close()
    return jsonify({"success": True, "user": user_details})


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully"})


@app.route('/api/auth/session', methods=['GET'])
def get_session():
    if 'user_id' not in session:
        return jsonify({"authenticated": False}), 401

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, role FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()

    if not user:
        session.clear()
        conn.close()
        return jsonify({"authenticated": False}), 401

    user_details = {
        "id": user['id'],
        "email": user['email'],
        "role": user['role'],
        "name": user['email'].split('@')[0].capitalize()
    }

    if user['role'] == 'student':
        cursor.execute("SELECT name FROM students WHERE user_id = ?", (user['id'],))
        student_prof = cursor.fetchone()
        if student_prof:
            user_details['name'] = student_prof['name']

    conn.close()
    return jsonify({"authenticated": True, "user": user_details})


# ----------------- Resume Upload API -----------------
@app.route('/api/students/resume/upload', methods=['POST'])
def upload_resume():
    if 'user_id' not in session or session['role'] != 'student':
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session['user_id']

    if 'resume' not in request.files:
        return jsonify({"error": "No file uploaded. Use field name 'resume'."}), 400

    file = request.files['resume']

    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    filename = f"resume_{user_id}.pdf"
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(save_path)

    resume_url = f"/api/resumes/{filename}"

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE students SET resume_link = ? WHERE user_id = ?", (resume_url, user_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "resume_link": resume_url}), 200
    except Exception as e:
        conn.close()
        return jsonify({"error": f"Database error: {str(e)}"}), 500


@app.route('/api/resumes/<filename>', methods=['GET'])
def serve_resume(filename):
    """Serves the uploaded PDF from the uploads/ directory. Accessible by logged-in users."""
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ----------------- Student Profile API -----------------
@app.route('/api/students/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'GET':
        cursor.execute("SELECT * FROM students WHERE user_id = ?", (user_id,))
        student = cursor.fetchone()
        conn.close()
        if not student:
            return jsonify({"error": "Profile not found"}), 404
        return jsonify(dict(student))

    # POST - update profile
    data = request.json
    if not data:
        conn.close()
        return jsonify({"error": "No data provided"}), 400

    try:
        # Fetch student's CURRENT profile BEFORE the update (to compare eligibility)
        cursor.execute("SELECT * FROM students WHERE user_id = ?", (user_id,))
        old_profile = cursor.fetchone()

        cursor.execute('''
            UPDATE students SET 
                name = ?, branch = ?, cgpa = ?, tenth_percent = ?, twelfth_percent = ?,
                active_backlogs = ?, history_backlogs = ?, graduation_year = ?, 
                skills = ?, resume_link = ?
            WHERE user_id = ?
        ''', (
            data['name'], data['branch'], float(data['cgpa']),
            float(data['tenth_percent']), float(data['twelfth_percent']),
            int(data.get('active_backlogs', 0)), int(data.get('history_backlogs', 0)),
            int(data['graduation_year']), data.get('skills', ''),
            data.get('resume_link', ''), user_id
        ))
        conn.commit()

        # EMAIL TRIGGER B: Check if student became newly eligible for any company
        cursor.execute("SELECT * FROM students WHERE user_id = ?", (user_id,))
        new_profile = cursor.fetchone()

        cursor.execute("SELECT u.email FROM users u WHERE u.id = ?", (user_id,))
        user_row = cursor.fetchone()
        student_with_email = dict(new_profile)
        student_with_email['email'] = user_row['email']

        cursor.execute("SELECT * FROM companies")
        all_companies = cursor.fetchall()

        notify_count = 0
        for company in all_companies:
            was_eligible = evaluate_eligibility(old_profile, company)['eligible']
            is_now_eligible = evaluate_eligibility(new_profile, company)['eligible']
            if not was_eligible and is_now_eligible:
                send_eligibility_email(student_with_email, dict(company))
                notify_count += 1

        conn.close()
        msg = "Profile updated successfully."
        if notify_count > 0:
            msg += f" You are now eligible for {notify_count} new company opportunity(s)! Check your email."
        return jsonify({"success": True, "message": msg})

    except Exception as e:
        conn.close()
        return jsonify({"error": f"Error updating profile: {str(e)}"}), 400


# ----------------- Companies & Eligibility API -----------------
@app.route('/api/companies', methods=['GET'])
def get_companies():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM companies")
    companies = [dict(c) for c in cursor.fetchall()]

    if 'user_id' in session and session['role'] == 'student':
        user_id = session['user_id']
        cursor.execute("SELECT * FROM students WHERE user_id = ?", (user_id,))
        student = cursor.fetchone()

        cursor.execute("SELECT company_id, status FROM applications WHERE student_id = ?", (user_id,))
        applied = {row['company_id']: row['status'] for row in cursor.fetchall()}

        if student:
            for company in companies:
                eval_res = evaluate_eligibility(student, company)
                company['eligibility'] = {
                    "eligible": eval_res['eligible'],
                    "reasons": eval_res['reasons']
                }
                company['applied_status'] = applied.get(company['id'], None)
        else:
            for company in companies:
                company['eligibility'] = {"eligible": False, "reasons": ["Profile not configured"]}
                company['applied_status'] = None
    else:
        for company in companies:
            company['eligibility'] = None
            company['applied_status'] = None

    conn.close()
    return jsonify(companies)


# ----------------- Job Applications API -----------------
@app.route('/api/applications/apply', methods=['POST'])
def apply():
    if 'user_id' not in session or session['role'] != 'student':
        return jsonify({"error": "Unauthorized. Only students can apply."}), 401

    student_id = session['user_id']
    data = request.json
    if not data or 'company_id' not in data:
        return jsonify({"error": "Company ID required"}), 400

    company_id = int(data['company_id'])

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE user_id = ?", (student_id,))
    student = cursor.fetchone()
    cursor.execute("SELECT * FROM companies WHERE id = ?", (company_id,))
    company = cursor.fetchone()

    if not student or not company:
        conn.close()
        return jsonify({"error": "Student or Company records missing"}), 404

    try:
        deadline_date = datetime.strptime(company['deadline'], "%Y-%m-%d")
        if datetime.now() > deadline_date:
            conn.close()
            return jsonify({"error": f"Application deadline ({company['deadline']}) has passed."}), 400
    except ValueError:
        pass

    eval_res = evaluate_eligibility(student, company)
    if not eval_res['eligible']:
        conn.close()
        return jsonify({
            "error": "You do not meet the eligibility criteria for this company.",
            "reasons": eval_res['reasons']
        }), 400

    cover_letter = data.get('cover_letter', '')
    preferred_location = data.get('preferred_location', '')

    try:
        cursor.execute("INSERT INTO applications (student_id, company_id, status, cover_letter, preferred_location) VALUES (?, ?, 'Applied', ?, ?)",
                       (student_id, company_id, cover_letter, preferred_location))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Applied successfully"})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "You have already applied to this company"}), 400


@app.route('/api/applications/student', methods=['GET'])
def get_student_applications():
    if 'user_id' not in session or session['role'] != 'student':
        return jsonify({"error": "Unauthorized"}), 401

    student_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT a.id as application_id, a.status, a.applied_at, c.name as company_name, c.role, c.package 
        FROM applications a 
        JOIN companies c ON a.company_id = c.id
        WHERE a.student_id = ?
        ORDER BY a.applied_at DESC
    ''', (student_id,))

    apps = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(apps)


# ----------------- TPO / Admin API Endpoints -----------------
@app.route('/api/admin/students', methods=['GET'])
def admin_get_students():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT s.*, u.email FROM students s JOIN users u ON s.user_id = u.id")
    students = [dict(s) for s in cursor.fetchall()]
    conn.close()
    return jsonify(students)


@app.route('/api/admin/applications', methods=['GET'])
def admin_get_applications():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT a.id as application_id, a.status, a.applied_at, a.cover_letter, a.preferred_location,
               s.name as student_name, s.roll_no, s.branch, s.cgpa, s.resume_link,
               c.name as company_name, c.role as company_role
        FROM applications a
        JOIN students s ON a.student_id = s.user_id
        JOIN companies c ON a.company_id = c.id
        ORDER BY a.applied_at DESC
    ''')
    apps = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(apps)


@app.route('/api/admin/applications/<int:app_id>', methods=['PUT'])
def admin_update_application_status(app_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    if not data or 'status' not in data:
        return jsonify({"error": "Status value required"}), 400

    status = data['status']
    if status not in ['Applied', 'Shortlisted', 'Rejected', 'Selected']:
        return jsonify({"error": "Invalid status value"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE applications SET status = ? WHERE id = ?", (status, app_id))

    if cursor.rowcount == 0:
        conn.close()
        return jsonify({"error": "Application record not found"}), 404

    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": f"Application status updated to '{status}'"})


@app.route('/api/admin/companies', methods=['POST'])
def admin_add_company():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    required = ['name', 'role', 'package', 'min_cgpa', 'min_tenth', 'min_twelfth', 'max_backlogs', 'deadline']
    for field in required:
        if field not in data or data[field] == '':
            return jsonify({"error": f"Field '{field}' is required"}), 400

    name = data['name']
    logo_color = data.get('logo_color', '#4f46e5')
    role = data['role']
    package = data['package']
    try:
        min_cgpa = float(data['min_cgpa'])
        min_tenth = float(data['min_tenth'])
        min_twelfth = float(data['min_twelfth'])
        max_backlogs = int(data['max_backlogs'])
    except ValueError:
        return jsonify({"error": "Criteria values must be numbers"}), 400

    allowed_branches = data.get('allowed_branches', 'All')
    deadline = data['deadline']

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO companies (name, logo_color, role, package, min_cgpa, min_tenth, min_twelfth, max_backlogs, allowed_branches, deadline)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, logo_color, role, package, min_cgpa, min_tenth, min_twelfth, max_backlogs, allowed_branches, deadline))

        new_company_id = cursor.lastrowid
        conn.commit()

        # EMAIL TRIGGER A: Notify all eligible students about the new company
        cursor.execute("SELECT * FROM companies WHERE id = ?", (new_company_id,))
        new_company = cursor.fetchone()

        cursor.execute('''
            SELECT s.*, u.email FROM students s 
            JOIN users u ON s.user_id = u.id
        ''')
        all_students = cursor.fetchall()

        email_count = 0
        for student in all_students:
            result = evaluate_eligibility(student, new_company)
            if result['eligible']:
                send_eligibility_email(dict(student), dict(new_company))
                email_count += 1

        conn.close()
        return jsonify({
            "success": True,
            "message": f"Company created successfully. Notified {email_count} eligible student(s)."
        }), 201

    except Exception as e:
        conn.close()
        return jsonify({"error": f"Database error: {str(e)}"}), 500


@app.route('/api/admin/companies/<int:company_id>', methods=['DELETE'])
def admin_delete_company(company_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM companies WHERE id = ?", (company_id,))
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({"error": "Company not found"}), 404

    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Company deleted successfully"})


@app.route('/api/admin/dashboard-stats', methods=['GET'])
def admin_dashboard_stats():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM companies")
    total_companies = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM applications")
    total_applications = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT student_id) FROM applications WHERE status = 'Selected'")
    placed_students = cursor.fetchone()[0]
    placement_rate = (placed_students / total_students * 100) if total_students > 0 else 0

    cursor.execute("SELECT AVG(cgpa) FROM students")
    avg_cgpa = cursor.fetchone()[0]
    avg_cgpa = round(avg_cgpa, 2) if avg_cgpa else 0.0

    cursor.execute("SELECT status, COUNT(*) as count FROM applications GROUP BY status")
    status_breakdown = {row['status']: row['count'] for row in cursor.fetchall()}
    for s in ['Applied', 'Shortlisted', 'Rejected', 'Selected']:
        if s not in status_breakdown:
            status_breakdown[s] = 0

    cursor.execute('''
        SELECT s.branch, COUNT(*) as total, SUM(CASE WHEN a.status = 'Selected' THEN 1 ELSE 0 END) as placed
        FROM students s
        LEFT JOIN applications a ON s.user_id = a.student_id
        GROUP BY s.branch
    ''')
    branch_stats = []
    for row in cursor.fetchall():
        branch_stats.append({
            "branch": row['branch'],
            "total": row['total'],
            "placed": row['placed']
        })

    conn.close()

    return jsonify({
        "stats": {
            "total_students": total_students,
            "total_companies": total_companies,
            "total_applications": total_applications,
            "placed_students": placed_students,
            "placement_rate": round(placement_rate, 1),
            "average_cgpa": avg_cgpa
        },
        "status_breakdown": status_breakdown,
        "branch_stats": branch_stats
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)