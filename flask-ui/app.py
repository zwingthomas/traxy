from flask import Flask, Response, render_template, redirect, url_for, request, session, flash, g
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

# maybe delete in the future
@app.route('/api/users/me', methods=['GET','PATCH'])
def proxy_users_me():
    token = session.get('token')
    headers = {}
    if token:
        headers['Authorization'] = f"Bearer {token}"
    if request.method == 'GET':
        upstream = requests.get(f"{API}/api/users/me", headers=headers)
    else:  # PATCH
        headers['Content-Type'] = 'application/json'
        upstream = requests.patch(f"{API}/api/users/me",
                                  headers=headers,
                                  json=request.get_json())
    return (upstream.content, upstream.status_code,
            [('Content-Type', upstream.headers.get('Content-Type',''))])


## Settings

def _auth_headers():
    token = session.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}

@app.route("/api/users/me/profile")
def proxy_get_profile():
    r = requests.get(f"{API}/api/users/me/profile",
                     headers=_auth_headers(), timeout=5)
    return (r.content, r.status_code, _strip_hop_by_hop(r.headers))

@app.route("/api/users/me/profile", methods=["PUT"])
def proxy_update_profile():
    r = requests.put(f"{API}/api/users/me/profile",
                     headers={**_auth_headers(),
                              "Content-Type": "application/json"},
                     json=request.get_json(force=True), timeout=5)
    return (r.content, r.status_code, _strip_hop_by_hop(r.headers))

@app.route("/api/users/me/password", methods=["PUT"])
def proxy_change_password():
    r = requests.put(f"{API}/api/users/me/password",
                     headers={**_auth_headers(),
                              "Content-Type": "application/json"},
                     json=request.get_json(force=True), timeout=5)
    return (r.content, r.status_code, _strip_hop_by_hop(r.headers))

def _strip_hop_by_hop(headers: requests.structures.CaseInsensitiveDict):
    """Remove headers that Flask/Gunicorn will set for us."""
    hop = {"Content-Encoding", "Content-Length", "Transfer-Encoding",
           "Connection"}
    return [(k, v) for k, v in headers.items() if k not in hop]

@app.route("/settings", methods=["GET", "POST"])
def settings():
    token = session.get("token")
    if not token:
        return redirect("/login")

    headers = {"Authorization": f"Bearer {token}"}

    if request.method == "POST":
        form = request.form.to_dict()

        # profile update
        profile_payload = {
            k: v for k, v in form.items()
            if k in ("first_name", "last_name", "email", "phone") and v
        }
        try:
            # <-- use PUT not PATCH here -->
            r = requests.put(
                f"{API}/api/users/me/profile",
                json=profile_payload,
                headers=headers,
                timeout=5,
            )
            r.raise_for_status()

            # password change
            old_pw = form.get("old_password")
            new_pw = form.get("new_password")
            if old_pw and new_pw:
                r2 = requests.put(
                    f"{API}/api/users/me/password",
                    json={"old_password": old_pw, "new_password": new_pw},
                    headers=headers,
                    timeout=5,
                )
                flash(
                  "Password changed." if r2.ok else "Error changing password",
                  "success" if r2.ok else "error"
                )

            flash("Profile updated.", "success")
        except requests.RequestException as exc:
            flash(f"Could not update profile: {exc}", "error")

        return redirect(url_for("settings"))

    # GET: load the current profile
    try:
        r = requests.get(
            f"{API}/api/users/me/profile", headers=headers, timeout=5
        )
        r.raise_for_status()
        profile = r.json()
    except requests.RequestException as exc:
        flash(f"Could not load profile: {exc}", "error")
        profile = {}

    return render_template("settings.html", profile=profile)

# Request password reset
@app.route("/forgot-password", methods=["GET","POST"])
def forgot_password():
    if request.method=="POST":
        email = request.form["email"]
        token = session.get("token")
        headers = {"Authorization":f"Bearer {token}"} if token else {}
        r = requests.post(
           f"{API}/password-reset/request",
           headers={**headers, "Content-Type":"application/json"},
           json={"email": email},
           timeout=5
        )
        flash("If that address exists, you’ll get an email shortly", "info")
        return redirect(url_for("login"))
    return render_template("forgot_password.html")


# Reset password form
@app.route("/reset-password", methods=["GET","POST"])
def reset_password():
    token = request.args.get("token") or request.form.get("token")
    if request.method=="POST":
        new_pw = request.form["new_password"]
        resp = requests.post(
          f"{API}/password-reset",
          headers={"Content-Type":"application/json"},
          json={"token": token, "new_password": new_pw},
          timeout=5
        )
        if resp.status_code == 200:
            flash("Your password has been reset. Please log in.", "success")
            return redirect(url_for("login"))
        else:
            flash("Invalid or expired link", "error")
    return render_template("reset_password.html", token=token)

## Trackers

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
    widget_type = request.form.get('widget_type')

    # Build the rule dict: { period: count }
    rule = { rule_period: rule_count }

    payload = {
        "name":       title,
        "color":      color,
        "rule":       rule,
        "visibility": visibility,
        "widget_type": widget_type
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
    
@app.route('/trackers/reorder', methods=['PUT'])
def proxy_reorder_trackers():
    token = session.get('token')
    if not token:
        return ("", 401)

    payload = request.get_json()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    r = requests.put(f"{API}/api/trackers/reorder",
                            json=payload,
                            headers=headers)

    if not r.ok:
        app.logger.error("Proxy PUT /trackers/reorder failed: %s %s",
                         r.status_code, r.text)

    return (r.content, r.status_code, r.headers.items())

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
    widget_type = request.form.get('widget_type')

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
        "visibility": visibility,
        "widget_type": widget_type
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

@app.route('/u/<username>')
def public_profile(username):
    try:
        token = session.get('token')
        headers = {}
        if token:
            headers['Authorization'] = f"Bearer {token}"

        r = requests.get(f"{API}/api/trackers/{username}/trackers", headers=headers)
        if r.status_code == 404:
            flash("User not found.", "warning")
            return redirect(url_for('index'))
        elif not r.ok:
            flash(f"Error fetching public profile: {r.status_code} — {r.text}", "error")
            return redirect(url_for('index'))
        trackers = r.json()

        friends = []
        are_friends = False
        r = requests.get(f"{API}/api/users/{username}/friends", headers=headers)
        if r.ok:
            are_friends = True
            friends = r.json()

    except requests.RequestException as e:
        flash(f"Error fetching public profile: {e}", "error")
        return redirect(url_for('index'))

    return render_template('user.html', username=username, friends=friends, trackers=trackers, are_friends=are_friends)

@app.route('/api/users/<username>/trackers')
def proxy_users_trackers(username):
    token = session.get('token')
    headers = {}
    if token:
        headers['Authorization'] = f"Bearer {token}"
    upstream = requests.get(f"{API}/api/trackers/{username}/trackers", headers=headers)
    return (upstream.content, upstream.status_code,
            [('Content-Type', upstream.headers.get('Content-Type',''))])

@app.route("/api/users/search")
def proxy_user_search():
    """
    Pass-through proxy to backend /api/users/search.

    Front-end calls:  /api/users/search?prefix=<string>
    FastAPI backend expects:  ?prefix=<string>
    """
    token = session.get("token")
    if not token:
        return ("", 401)

    # read query-string exactly as the browser sent it
    prefix = request.args.get("prefix", "")
    limit  = request.args.get("limit", "10")      # optional – default=10

    headers =  {"Authorization": f"Bearer {token}",
                "Accept-Encoding": "identity"}

    try:
        r = requests.get(
            f"{API}/api/users/search",
            params={"prefix": prefix, "limit": limit},
            headers=headers,
            timeout=5,
        )
        return (r.text, r.status_code, r.headers.items())
    except requests.RequestException as e:
        return (str(e), 502)
    
@app.route("/api/users/<username>/friends")
def proxy_read_friends(username: str):
    token   = session.get("token")         # may be None for anonymous
    headers = {
        "Accept-Encoding": "identity",
        **({"Authorization": f"Bearer {token}"} if token else {})
    }

    try:
        r = requests.get(f"{API}/api/users/{username}/friends",
                         headers=headers, timeout=5)
    except requests.RequestException as exc:
        return str(exc), 502

    # ▸ Return **decoded** body and strip CE / length headers
    hop_by_hop = {
        "Content-Encoding",
        "Content-Length",
        "Transfer-Encoding",
        "Connection",
    }
    clean_headers = [(k, v) for k, v in r.headers.items() if k.lower() not in hop_by_hop]
    return r.content, r.status_code, clean_headers


@app.route("/api/users/<username>/friends", methods=["POST"])
def proxy_add_friend(username):
    token = session.get("token")
    if not token:
        return ("", 401)

    r = requests.post(f"{API}/api/users/{username}/friends",
                      headers={"Authorization": f"Bearer {token}"})
    return (r.text, r.status_code, r.headers.items())

@app.route("/api/users/<username>/friends", methods=["DELETE"])
def proxy_delete_friend(username):
    token = session.get("token")
    if not token:
        return ("", 401)
    r = requests.delete(
        f"{API}/api/users/{username}/friends?username={request.args.get('username')}",
        headers={"Authorization": f"Bearer {token}"}
    )
    return (r.text, r.status_code, r.headers.items())

@app.context_processor
def inject_current_user():
    token = session.get('token')
    user = None
    if token:
        try:
            # Ask API for the current user
            resp = requests.get(
                f"{API}/api/users/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            if resp.ok:
                user = resp.json()
        except requests.RequestException:
            pass
    return {"current_user": user}

if __name__ == '__main__':
    app.run(debug=True)