from flask import Flask, Response, render_template, redirect, url_for, request, session, flash
import os, requests

app = Flask(__name__)
app.secret_key = os.environ['FLASK_SECRET_KEY'] 
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