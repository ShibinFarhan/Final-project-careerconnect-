# Quick action routes for recruiter dashboard
# To be added to app.py after delete_job route

routes_code = '''
@app.route("/recruiter/all_candidates")
@login_required(role="recruiter")
def all_candidates():
    user_id = session.get("user_id")
    conn = get_db()
    cursor = conn.cursor()

    recruiter = cursor.execute('SELECT id FROM recruiters WHERE user_id = ?', (user_id,)).fetchone()
    if not recruiter:
        conn.close()
        flash("Recruiter profile not found.", "error")
        return redirect(url_for("recruiter_dashboard"))

    # Fetch all candidates who applied to recruiter's jobs
    candidates = cursor.execute(
        """
        SELECT DISTINCT
               js.id as seeker_id, js.full_name, js.email,
               js.primary_skills, js.experience_years, js.user_id,
               COUNT(a.id) as application_count
        FROM applications a
        JOIN job_postings jp ON a.job_id = jp.id
        JOIN job_seekers js ON a.seeker_id = js.id
        WHERE jp.recruiter_id = ?
        GROUP BY js.id
        ORDER BY js.full_name
        """,
        (recruiter['id'],),
    ).fetchall()

    # Compute ATS scores for all candidates
    candidate_ats_scores = {}
    for candidate in candidates:
        try:
            resume = cursor.execute(
                'SELECT filename FROM resumes WHERE user_id = ?',
                (candidate['user_id'],)
            ).fetchone()
            
            if resume:
                resume_path = os.path.join(app.config['UPLOAD_FOLDER'], resume['filename'])
                if os.path.exists(resume_path):
                    analysis_result = analyzer.analyze_resume_file(
                        resume_path,
                        profile_skills=candidate['primary_skills'] or '',
                        experience_years=candidate['experience_years'] or 0,
                    )
                    if analysis_result and 'ats' in analysis_result:
                        candidate_ats_scores[candidate['seeker_id']] = analysis_result['ats']['ats_score']
        except Exception:
            pass

    conn.close()
    return render_template("all_candidates.html", candidates=candidates or [], candidate_ats_scores=candidate_ats_scores)

@app.route("/recruiter/all_shortlisted")
@login_required(role="recruiter")
def all_shortlisted():
    user_id = session.get("user_id")
    conn = get_db()
    cursor = conn.cursor()

    recruiter = cursor.execute('SELECT id FROM recruiters WHERE user_id = ?', (user_id,)).fetchone()
    if not recruiter:
        conn.close()
        flash("Recruiter profile not found.", "error")
        return redirect(url_for("recruiter_dashboard"))

    # Fetch all shortlisted candidates
    candidates = cursor.execute(
        """
        SELECT a.id as application_id,
               js.full_name, js.email, js.user_id as seeker_user_id,
               js.primary_skills, js.experience_years,
               jp.job_title, a.applied_at
        FROM applications a
        JOIN job_postings jp ON a.job_id = jp.id
        JOIN job_seekers js ON a.seeker_id = js.id
        WHERE jp.recruiter_id = ? AND a.status = 'shortlisted'
        ORDER BY a.applied_at DESC
        """,
        (recruiter['id'],),
    ).fetchall()

    # Compute ATS scores
    candidate_ats_scores = {}
    for candidate in candidates:
        try:
            resume = cursor.execute(
                'SELECT filename FROM resumes WHERE user_id = ?',
                (candidate['seeker_user_id'],)
            ).fetchone()
            
            if resume:
                resume_path = os.path.join(app.config['UPLOAD_FOLDER'], resume['filename'])
                if os.path.exists(resume_path):
                    analysis_result = analyzer.analyze_resume_file(
                        resume_path,
                        profile_skills=candidate['primary_skills'] or '',
                        experience_years=candidate['experience_years'] or 0,
                    )
                    if analysis_result and 'ats' in analysis_result:
                        candidate_ats_scores[candidate['application_id']] = analysis_result['ats']['ats_score']
        except Exception:
            pass

    conn.close()
    return render_template("all_shortlisted.html", candidates=candidates or [], candidate_ats_scores=candidate_ats_scores)

@app.route("/recruiter/analytics")
@login_required(role="recruiter")
def analytics():
    user_id = session.get("user_id")
    conn = get_db()
    cursor = conn.cursor()

    recruiter = cursor.execute('SELECT id FROM recruiters WHERE user_id = ?', (user_id,)).fetchone()
    if not recruiter:
        conn.close()
        flash("Recruiter profile not found.", "error")
        return redirect(url_for("recruiter_dashboard"))

    # Get various analytics metrics
    total_jobs = cursor.execute(
        'SELECT COUNT(*) as count FROM job_postings WHERE recruiter_id = ?',
        (recruiter['id'],)
    ).fetchone()['count']
    
    active_jobs = cursor.execute(
        'SELECT COUNT(*) as count FROM job_postings WHERE recruiter_id = ? AND is_active = 1',
        (recruiter['id'],)
    ).fetchone()['count']
    
    total_applications = cursor.execute(
        """
        SELECT COUNT(*) as count FROM applications a
        JOIN job_postings jp ON a.job_id = jp.id
        WHERE jp.recruiter_id = ?
        """,
        (recruiter['id'],)
    ).fetchone()['count']
    
    shortlisted = cursor.execute(
        """
        SELECT COUNT(*) as count FROM applications a
        JOIN job_postings jp ON a.job_id = jp.id
        WHERE jp.recruiter_id = ? AND a.status = 'shortlisted'
        """,
        (recruiter['id'],)
    ).fetchone()['count']
    
    rejected = cursor.execute(
        """
        SELECT COUNT(*) as count FROM applications a
        JOIN job_postings jp ON a.job_id = jp.id
        WHERE jp.recruiter_id = ? AND a.status = 'rejected'
        """,
        (recruiter['id'],)
    ).fetchone()['count']
    
    hired = cursor.execute(
        """
        SELECT COUNT(*) as count FROM applications a
        JOIN job_postings jp ON a.job_id = jp.id
        WHERE jp.recruiter_id = ? AND a.status = 'hired'
        """,
        (recruiter['id'],)
    ).fetchone()['count']

    conn.close()

    analytics_data = {
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'total_applications': total_applications,
        'shortlisted': shortlisted,
        'rejected': rejected,
        'hired': hired,
        'conversion_rate': round((hired / max(total_applications, 1)) * 100, 1) if total_applications > 0 else 0,
    }

    return render_template("analytics.html", analytics=analytics_data)
'''
