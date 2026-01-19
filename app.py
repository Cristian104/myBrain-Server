from flask import Flask, render_template, request, redirect, session, url_for

app = Flask(__name__)
app.secret_key = 'CHANGE_THIS_TO_RANDOM_LETTERS'  # Important for security

# --- CONFIGURATION ---
USERNAME = "jorg"
PASSWORD = "yourpassword123"  # <--- SET YOUR DESIRED PASSWORD HERE
# ---------------------

@app.route('/', methods=['GET', 'POST'])
def login():
    # If user is already logged in, show dashboard
    if session.get('logged_in'):
        return render_template('dashboard.html')

    error = None
    if request.method == 'POST':
        if request.form['username'] == USERNAME and request.form['password'] == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('login'))
        else:
            error = 'Invalid Credentials. Access Denied.'

    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
