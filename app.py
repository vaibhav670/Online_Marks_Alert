from flask import Flask, request, render_template, redirect, url_for, flash
from twilio.rest import Client
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necessary for flashing messages

# Configure Twilio
account_sid = 'AC7d7f67f9104db3d57e1db78b86620263'
auth_token = 'a6c40201aee55fb25299e97a5f897e95'
twilio_number = '+13148046027'
client = Client(account_sid, auth_token)

# Function to send SMS using Twilio
def send_sms(to, message):
    try:
        message = client.messages.create(
            body=message,
            from_=twilio_number,
            to=to
        )
        print(f"Message sent with SID: {message.sid}")
        return True
    except Exception as e:
        print(f"Failed to send SMS: {e}")
        return False

# Function to fetch student information from SQLite database
def get_student_info(student_id):
    try:
        conn = sqlite3.connect('school.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name, parent_contact FROM students WHERE student_id=?", (student_id,))
        student = cursor.fetchone()
        conn.close()
        if student:
            return {"name": student[0], "parent_contact": student[1]}
        else:
            return None
    except Exception as e:
        print(f"Failed to fetch student info: {e}")
        return None

# Route for the home page
@app.route('/')
def index():
    return "Welcome to the Online Student Marks Alerting System!"

# Route for handling marks submission
@app.route('/marks', methods=['GET', 'POST'])
def marks():
    if request.method == 'POST':
        try:
            student_id = request.form['student_id']
            subject = request.form['subject']
            mark = int(request.form['mark'])
            
            # Fetch student information from database
            student = get_student_info(student_id)
            if not student:
                flash('Student not found. Please check the student ID.', 'danger')
                return redirect(url_for('marks'))
            
            # Process marks and send alert if mark is below threshold
            if mark < 50:
                message = f"Alert: Your child {student['name']} scored {mark} in {subject}."
                if send_sms(student['parent_contact'], message):
                    flash('Alert SMS sent successfully!', 'success')
                else:
                    flash('Failed to send alert SMS. Please try again later.', 'danger')
            
            # Save marks to database
            conn = sqlite3.connect('school.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO marks (student_id, subject, mark) VALUES (?, ?, ?)",
                           (student_id, subject, mark))
            conn.commit()
            conn.close()
            
            flash('Marks submitted successfully!', 'success')
            return redirect(url_for('marks'))
        except Exception as e:
            print(f"Error processing form: {e}")
            flash('An error occurred while submitting the form. Please try again.', 'danger')
            return redirect(url_for('marks'))
    
    return render_template('marks.html')

# Optionally, handle favicon requests
@app.route('/favicon.ico')
def favicon():
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)
