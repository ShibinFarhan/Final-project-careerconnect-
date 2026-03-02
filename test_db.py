import sqlite3

conn = sqlite3.connect('careerconnect.db', timeout=10.0)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Test admin_seekers query
print('Testing admin_seekers query...')
try:
    seekers = cursor.execute('''
        SELECT u.id, u.username, u.created_at,
               js.full_name, js.email, js.education, js.experience_years, js.primary_skills
        FROM users u
        JOIN job_seekers js ON u.id = js.user_id
        WHERE u.role = "seeker"
        ORDER BY u.created_at DESC
    ''').fetchall()
    print(f'Seekers query OK: {len(seekers)} seekers found')
except Exception as e:
    print(f'Seekers query ERROR: {e}')

# Test admin_recruiters query
print('Testing admin_recruiters query...')
try:
    recruiters = cursor.execute('''
        SELECT u.id, u.username, u.created_at,
               r.company_name, r.industry_type, r.company_location
        FROM users u
        JOIN recruiters r ON u.id = r.user_id
        WHERE u.role = "recruiter"
        ORDER BY u.created_at DESC
    ''').fetchall()
    print(f'Recruiters query OK: {len(recruiters)} recruiters found')
except Exception as e:
    print(f'Recruiters query ERROR: {e}')

# Test admin_jobs query
print('Testing admin_jobs query...')
try:
    jobs = cursor.execute('''
        SELECT jp.*, r.company_name,
               COUNT(a.id) as application_count
        FROM job_postings jp
        LEFT JOIN recruiters r ON jp.recruiter_id = r.id
        LEFT JOIN applications a ON jp.id = a.job_id
        GROUP BY jp.id
        ORDER BY jp.created_at DESC
    ''').fetchall()
    print(f'Jobs query OK: {len(jobs)} jobs found')
except Exception as e:
    print(f'Jobs query ERROR: {e}')
    
conn.close()
