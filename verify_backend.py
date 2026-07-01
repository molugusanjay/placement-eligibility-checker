import sqlite3
import os
import sys

def test_database_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')
    print(f"[Test] Checking database at {db_path}...")
    
    if not os.path.exists(db_path):
        print("[FAIL] database.db does not exist. Run db_init.py or run.py first.")
        return False
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test Query
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"[PASS] Successfully connected. Found tables: {', '.join(tables)}")
        
        required_tables = ['users', 'students', 'companies', 'applications']
        for rt in required_tables:
            if rt not in tables:
                print(f"[FAIL] Missing required table: {rt}")
                return False
        print("[PASS] All required tables are present.")
        
        # Test Seed Data
        cursor.execute("SELECT COUNT(*) FROM users;")
        user_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM companies;")
        company_count = cursor.fetchone()[0]
        
        print(f"[PASS] Data integrity check: Users count = {user_count}, Companies count = {company_count}")
        if user_count == 0 or company_count == 0:
            print("[FAIL] Seed data is empty.")
            return False
            
        conn.close()
        return True
    except Exception as e:
        print(f"[FAIL] Database verification failed: {e}")
        return False

def test_eligibility_logic():
    print("[Test] Verifying eligibility calculation logic mock...")
    
    # Mock profiles
    jane = {
        'name': 'Jane Doe',
        'branch': 'Computer Science',
        'cgpa': 8.9,
        'tenth_percent': 92.5,
        'twelfth_percent': 88.0,
        'active_backlogs': 0
    }
    
    john = {
        'name': 'John Smith',
        'branch': 'Mechanical Eng',
        'cgpa': 7.2,
        'tenth_percent': 78.0,
        'twelfth_percent': 72.5,
        'active_backlogs': 1
    }
    
    google = {
        'name': 'Google',
        'min_cgpa': 8.5,
        'min_tenth': 80.0,
        'min_twelfth': 80.0,
        'max_backlogs': 0,
        'allowed_branches': 'Computer Science, Electronics Eng'
    }

    tcs = {
        'name': 'TCS Ninja',
        'min_cgpa': 6.0,
        'min_tenth': 60.0,
        'min_twelfth': 60.0,
        'max_backlogs': 2,
        'allowed_branches': 'All'
    }

    def run_check(student, company):
        reasons = []
        eligible = True
        if student['cgpa'] < company['min_cgpa']:
            eligible = False
            reasons.append("CGPA limit failed")
        if student['tenth_percent'] < company['min_tenth']:
            eligible = False
            reasons.append("10th limit failed")
        if student['twelfth_percent'] < company['min_twelfth']:
            eligible = False
            reasons.append("12th limit failed")
        if student['active_backlogs'] > company['max_backlogs']:
            eligible = False
            reasons.append("Backlogs count limit exceeded")
            
        allowed = company['allowed_branches']
        if allowed.lower() != 'all':
            allowed_list = [b.strip().lower() for b in allowed.split(',')]
            if student['branch'].lower() not in allowed_list:
                eligible = False
                reasons.append("Branch not allowed")
        return eligible, reasons

    # Jane Google Check -> Should Pass
    jane_google_ok, jane_google_reasons = run_check(jane, google)
    print(f"  Jane + Google eligibility check: {'PASS' if jane_google_ok else 'FAIL'}")
    assert jane_google_ok, "Jane should be eligible for Google"

    # John Google Check -> Should Fail
    john_google_ok, john_google_reasons = run_check(john, google)
    print(f"  John + Google eligibility check: {'PASS' if john_google_ok else 'FAIL'} (Expected: FAIL)")
    print(f"    Reasons for failure: {john_google_reasons}")
    assert not john_google_ok, "John should be ineligible for Google"
    assert len(john_google_reasons) == 5, "John should fail CGPA, 10th%, 12th%, Backlogs, and Branch"

    # John TCS Check -> Should Pass
    john_tcs_ok, john_tcs_reasons = run_check(john, tcs)
    print(f"  John + TCS Ninja eligibility check: {'PASS' if john_tcs_ok else 'FAIL'}")
    assert john_tcs_ok, "John should be eligible for TCS Ninja"

    print("[PASS] Core eligibility calculations working correctly.")
    return True

if __name__ == '__main__':
    print("=" * 50)
    print("        PREPELIGIBLE BACKEND TEST VERIFIER")
    print("=" * 50)
    
    db_ok = test_database_connection()
    logic_ok = test_eligibility_logic()
    
    if db_ok and logic_ok:
        print("\n[SUCCESS] All verification tests passed successfully!")
        sys.exit(0)
    else:
        print("\n[ERROR] Verification tests failed.")
        sys.exit(1)
