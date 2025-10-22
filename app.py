from flask import Flask, request, jsonify
import mysql.connector
from datetime import datetime

app = Flask(__name__)

# ===== DATABASE CONNECTION =====
def get_db_connection():
    return mysql.connector.connect(
        host="shuttle.proxy.rlwy.net",
        user="root",
        password="JCfNOSYEIrgNDqxwzaHBEufEJDPLQkKU",
        database="railway",
        port=40148,
        ssl_disabled=True
    )


# ====== 1️⃣ GET FAQ ANSWER ======
@app.route('/faqs', methods=['GET'])
def get_faq():
    """Fetch answer from FAQs table"""
    question = request.args.get('question', '')
    if not question:
        return jsonify({'error': 'No question provided'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT answer FROM faqs WHERE question LIKE %s LIMIT 1", (f"%{question}%",))
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if result:
        return jsonify({'answer': result['answer'], 'source': 'database'})
    else:
        return jsonify({'answer': None, 'source': 'not_found'})

# ====== 2️⃣ SAVE UNANSWERED QUESTION ======
@app.route('/unanswered_questions', methods=['POST'])
def save_unanswered():
    """Save an unanswered question for later review"""
    try:
        from datetime import datetime  # Import datetime here
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        question = data.get('question', '').strip()
        if not question:
            return jsonify({'error': 'No question provided'}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
            
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO unanswered_questions (question, created_at)
            VALUES (%s, %s)
        """, (question, datetime.now()))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'status': 'saved', 
            'question': question
        }), 200
        
    except Exception as e:
        print(f"Error saving unanswered question: {e}")
        return jsonify({
            'error': 'Failed to save question',
            'details': str(e)
        }), 500

# ====== 2️⃣.5️⃣ GET ALL UNANSWERED QUESTIONS ======
@app.route('/unanswered_questions', methods=['GET'])
def get_unanswered():
    """Fetch all unanswered questions"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM unanswered_questions ORDER BY created_at DESC")
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify({'unanswered_questions': results})

# ====== 3️⃣ GET STUDENT FEEDBACK COUNTS ======
@app.route('/student_feedback_counts', methods=['GET'])
def get_feedback_counts():
    """Fetch all student feedback counts for recommendation"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM student_feedback_counts")
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({'feedback_counts': results})


# ====== 3️⃣.5️⃣ ADD STUDENT FEEDBACK COUNT ======
@app.route('/student_feedback_counts', methods=['POST'])
def add_feedback_count():
    """Add new feedback count record"""
    data = request.get_json()

    student_id = data.get('student_id')
    feedback_type = data.get('feedback_type')
    count = data.get('count', 1)

    if not student_id or not feedback_type:
        return jsonify({'error': 'Missing required fields'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO student_feedback_counts (student_id, feedback_type, count, created_at)
        VALUES (%s, %s, %s, %s)
    """, (student_id, feedback_type, count, datetime.now()))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'status': 'added', 'student_id': student_id, 'feedback_type': feedback_type})


# ====== 4️⃣ HEALTH CHECK ======
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})


# ====== APP RUNNER ======
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


