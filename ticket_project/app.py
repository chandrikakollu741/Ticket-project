from flask import Flask, render_template, request, redirect, url_for
import re, datetime, random, sqlite3

app = Flask(__name__)

# Initialize database
def init_db():
    conn = sqlite3.connect('tickets.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tickets
                 (ticket_id TEXT PRIMARY KEY, name TEXT, contact TEXT, 
                  ticket TEXT, category TEXT, date TEXT, priority TEXT, 
                  sentiment TEXT, solution TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Helpers
def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    return text

def detect_priority(text):
    high_words = ["urgent", "asap", "immediately", "not working", "important"]
    for word in high_words:
        if word in text:
            return "High"
    return "Normal"

def detect_sentiment(text):
    positive_words = ["thank you", "good", "happy", "great"]
    negative_words = ["problem", "issue", "not working", "bad", "error"]
    for word in positive_words:
        if word in text:
            return "Positive"
    for word in negative_words:
        if word in text:
            return "Negative"
    return "Neutral"

def generate_ticket_id():
    now = datetime.datetime.now()
    random_number = random.randint(100, 999)
    return f"TKT{now.strftime('%Y%m%d')}{random_number}"

# Home page
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form['name']
        contact = request.form['contact']
        ticket = request.form['ticket']
        category = request.form['category']
        date = request.form['date']

        cleaned_ticket = clean_text(ticket)
        priority = detect_priority(cleaned_ticket)
        sentiment = detect_sentiment(cleaned_ticket)
        ticket_id = generate_ticket_id()

        # Save ticket
        conn = sqlite3.connect('tickets.db')
        c = conn.cursor()
        c.execute('''INSERT INTO tickets 
                     (ticket_id, name, contact, ticket, category, date, priority, sentiment, solution)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (ticket_id, name, contact, cleaned_ticket, category, date, priority, sentiment, ""))
        conn.commit()
        conn.close()

        # Redirect to ticket details page
        return redirect(url_for('ticket_details', ticket_id=ticket_id))
    return render_template('index.html')

# Ticket details page
@app.route('/ticket/<ticket_id>')
def ticket_details(ticket_id):
    conn = sqlite3.connect('tickets.db')
    c = conn.cursor()
    c.execute("SELECT * FROM tickets WHERE ticket_id=?", (ticket_id,))
    ticket = c.fetchone()
    conn.close()

    if ticket:
        date_obj = datetime.datetime.strptime(ticket[5], "%Y-%m-%d")
        year = date_obj.year
        month = date_obj.month
        weekday = date_obj.strftime("%A")
        return render_template('ticket_details.html',
                               ticket=ticket,
                               year=year,
                               month=month,
                               weekday=weekday)
    else:
        return "Ticket not found!"

# All tickets page
@app.route('/tickets')
def tickets():
    conn = sqlite3.connect('tickets.db')
    c = conn.cursor()
    c.execute("SELECT * FROM tickets")
    all_tickets = c.fetchall()
    conn.close()
    return render_template('tickets.html', tickets=all_tickets)

# Add solution page
@app.route('/solve/<ticket_id>', methods=['GET', 'POST'])
def solve(ticket_id):
    conn = sqlite3.connect('tickets.db')
    c = conn.cursor()
    if request.method == 'POST':
        solution = request.form['solution']
        c.execute("UPDATE tickets SET solution=? WHERE ticket_id=?", (solution, ticket_id))
        conn.commit()
        conn.close()
        return "✅ Solution added successfully! <a href='/tickets'>Go back</a>"

    c.execute("SELECT * FROM tickets WHERE ticket_id=?", (ticket_id,))
    ticket = c.fetchone()
    conn.close()
    return render_template('solve.html', ticket=ticket)

if __name__ == '__main__':
    app.run(debug=True)