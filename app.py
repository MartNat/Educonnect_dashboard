from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    # Serve the dashboard page
    return render_template("index.html")

@app.route("/profile")
def profile():
    # Serve the student profile page
    return render_template("profile.html")

@app.route("/applications")
def applications():
    # Serve the applications page
    return render_template("applications.html")

@app.route("/analytics")
def analytics():
    # Serve the analytics page
    return render_template("analytics.html")

@app.route("/tasks")
def tasks():
    # Serve the tasks management page
    return render_template("tasks.html")

if __name__ == "__main__":
    app.run(debug=True)