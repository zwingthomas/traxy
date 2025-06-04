from flask import Flask, Response, render_template, redirect, url_for, request, session, flash
import os, requests
import secrets_manager

app = Flask(__name__)
app.secret_key = secrets_manager.get_secret('FRONTEND_SECRET_KEY')
API = os.getenv('API_BASE_URL')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'width="16" height="16" viewBox="0 0 16 16">'
        '<rect width="16" height="16" fill="#00ff00"/>'
        '</svg>'
    )
    return Response(svg, mimetype='image/svg+xml')

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        data = request.form.to_dict()
        try:
            r = requests.post(f"{API}/api/auth/signup", json=data)
            if r.ok:
                flash("Signup successful! Please log in.", "success")
                return redirect(url_for('login'))
            else:
                flash(f"Signup failed: {r.status_code} — {r.text}", "error")
        except requests.RequestException as e:
            flash(f"Signup error: {e}", "error")
    return render_template('signup.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        creds = request.form.to_dict()
        try:
            r = requests.post(f"{API}/api/auth/login", json=creds)
            if r.ok:
                session['token'] = r.json().get('access_token')
                flash("Logged in successfully.", "success")
                return redirect(url_for('dashboard'))
            else:
                flash(f"Login failed: {r.status_code} — {r.text}", "error")
        except requests.RequestException as e:
            flash(f"Login error: {e}", "error")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('token', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route('/api/trackers')
def proxy_get_trackers():
    token = session.get('token')
    if not token:
        return ("", 401)
    headers = {"Authorization": f"Bearer {token}"}
    upstream = requests.get(f"{API}/api/trackers", headers=headers)

    if not upstream.ok:
        app.logger.error("Proxy GET /trackers failed: %s %s", upstream.status_code, upstream.text)

    # Builds a fresh Flask Response with raw bytes and only the Content-Type
    resp = Response(
        upstream.content,
        status=upstream.status_code,
        content_type=upstream.headers.get("Content-Type", "application/json"),
    )
    return resp

@app.route('/dashboard')
def dashboard():
    token = session.get('token')
    if not token:
        flash("Please log in to view your dashboard.", "warning")
        return redirect(url_for('login'))

    headers = {'Authorization': f'Bearer {token}'}
    user, trackers = {}, []
    # Fetch user info
    try:
        user_resp = requests.get(f"{API}/api/users/me", headers=headers)
        if user_resp.ok:
            user = user_resp.json()
        else:
            flash(f"Error fetching user info: {user_resp.status_code} — {user_resp.text}", "error")
    except requests.RequestException as e:
        flash(f"Error fetching user info: {e}", "error")

    # Fetch trackers
    try:
        tr_resp = requests.get(f"{API}/api/trackers", headers=headers)
        if tr_resp.ok:
            trackers = tr_resp.json()
        else:
            flash(f"Error fetching trackers: {tr_resp.status_code} — {tr_resp.text}", "error")
    except requests.RequestException as e:
        flash(f"Error fetching trackers: {e}", "error")

    return render_template('dashboard.html', user=user, trackers=trackers)

@app.route('/new-tracker', methods=['POST'])
def new_tracker():
    token = session.get('token')
    if not token:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))

    # Gather form inputs
    title       = request.form.get('title')
    color       = request.form.get('color')
    rule_count  = int(request.form.get('rule_count', 1))
    rule_period = request.form.get('rule_period')
    visibility  = request.form.get('visibility')

    # Build the rule dict: { period: count }
    rule = { rule_period: rule_count }

    payload = {
        "name":       title,
        "color":      color,
        "rule":       rule,
        "visibility": visibility
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json"
    }

    try:
        r = requests.post(f"{API}/api/trackers", json=payload, headers=headers)
        if r.ok:
            flash("Tracker created successfully!", "success")
        else:
            flash(f"Error creating tracker: {r.status_code} — {r.text}", "error")
    except requests.RequestException as e:
        flash(f"Error creating tracker: {e}", "error")

    return redirect(url_for('dashboard'))

@app.route('/delete-tracker/<int:tid>', methods=['DELETE'])
def delete_tracker_proxy(tid):
    token = session.get('token')
    if not token:
        return ("", 401)
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.delete(f"{API}/api/trackers/{tid}", headers=headers)
        return (r.text, r.status_code, r.headers.items())
    except requests.RequestException as e:
        flash(f"Error deleting tracker: {e}", "error")
        return (str(e), 500)

@app.route('/record-activity', methods=['POST'])
def record_activity_proxy():
    token = session.get('token')
    if not token:
        return ("", 401)

    payload = request.get_json()
    headers = {
      "Authorization": f"Bearer {token}",
      "Content-Type": "application/json"
    }
    try:
        r = requests.post(f"{API}/api/activities", json=payload, headers=headers)
        return (r.text, r.status_code, r.headers.items())
    except requests.RequestException as e:
        return (str(e), 500)
    
@app.route('/api/activities/reset', methods=['DELETE'])
def proxy_reset_activity():
    token = session.get("token")
    if not token:
        return ("", 401)

    tracker_id = request.args.get("tracker_id")
    if not tracker_id:
        return ("Missing tracker_id", 400)
    
    day = request.args.get("day")
    if not day:
        return ("Missing day", 400)

    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.delete(f"{API}/api/activities/reset?tracker_id={tracker_id}&day={day}", headers=headers)
        return (r.text, r.status_code, r.headers.items())
    except requests.RequestException as e:
        flash(f"Error reseting today's activity: {e}", "error")
        return (str(e), 500)

@app.route('/update-tracker/<int:tid>', methods=['POST'])
def update_tracker_proxy(tid):
    token = session.get('token')
    if not token:
        return ("", 401)

    # Read form‐encoded fields:
    title       = request.form.get('title')
    color       = request.form.get('color')
    rule_count  = request.form.get('rule_count')
    rule_period = request.form.get('rule_period')
    visibility  = request.form.get('visibility')

    # Basic checks:
    if not (title and color and rule_count and rule_period and visibility):
        flash("Missing required fields", "error")
        return redirect(url_for('dashboard'))

    try:
        count = int(rule_count)
    except ValueError:
        flash("Invalid goal count", "error")
        return redirect(url_for('dashboard'))

    # Build JSON payload exactly as FastAPI expects:
    payload = {
        "name":       title,
        "color":      color,
        "rule":       {rule_period: count},
        "visibility": visibility
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json"
    }

    try:
        r = requests.put(f"{API}/api/trackers/{tid}", json=payload, headers=headers)
        if r.status_code >= 200 and r.status_code < 300:
            # On success, redirect the user back to the dashboard
            return redirect(url_for('dashboard'))
        else:
            flash(f"Update failed: {r.status_code} {r.text}", "error")
            return redirect(url_for('dashboard'))
    except requests.RequestException as e:
        flash(f"Error updating tracker metadata: {e}", "error")
        return redirect(url_for('dashboard'))

@app.route('/<username>')
def public_profile(username):
    try:
        r = requests.get(
            f"{API}/api/users/{username}/trackers?visibility=public,friends"
        )
        if r.status_code == 404:
            flash("User not found.", "warning")
            return redirect(url_for('index'))
        elif not r.ok:
            flash(f"Error fetching public profile: {r.status_code} — {r.text}", "error")
            return redirect(url_for('index'))
        trackers = r.json()
    except requests.RequestException as e:
        flash(f"Error fetching public profile: {e}", "error")
        return redirect(url_for('index'))

    return render_template('user.html', username=username, trackers=trackers)

if __name__ == '__main__':
    app.run(debug=True)