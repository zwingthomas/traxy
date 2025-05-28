from flask import Flask, render_template, redirect, url_for, request, session
import os, requests
app = Flask(__name__)
app.secret_key = os.environ['FLASK_SECRET_KEY'] 
API = os.getenv('API_BASE_URL')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        data = request.form.to_dict()
        r = requests.post(f"{API}/api/auth/signup", json=data)
        if r.ok:
            return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        creds = request.form.to_dict()
        r = requests.post(f"{API}/api/auth/login", json=creds)
        if r.ok:
            session['token'] = r.json()['access_token']
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    token = session.get('token')
    if not token:
        return redirect(url_for('login'))
    headers = {'Authorization': f'Bearer {token}'}
    user_resp = requests.get(f"{API}/api/users/me", headers=headers)
    trackers_resp = requests.get(f"{API}/api/trackers", headers=headers)
    return render_template('dashboard.html', user=user_resp.json(), trackers=trackers_resp.json())

@app.route('/<username>')
def public_profile(username):
    # fetch public & friends-only trackers
    r = requests.get(f"{API}/api/users/{username}/trackers?visibility=public,friends")
    if r.status_code == 404:
        return "User not found", 404
    return render_template('user.html', username=username, trackers=r.json())

if __name__ == '__main__':
    app.run(debug=True)