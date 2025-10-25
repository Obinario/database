from flask import Flask, request, jsonify
import mysql.connector
from datetime import datetime
from flask import Flask, request, jsonify, render_template


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
        
# ====== 1️⃣ GET FAQ QUESTIONS ======
@app.route('/faqs/list', methods=['GET'])
def get_all_faqs():
    """Get all FAQs for suggestions"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, question, answer FROM faqs ORDER BY id")
        faqs = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'faqs': faqs,
            'count': len(faqs)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ====== 2️⃣ SAVE UNANSWERED QUESTION ======
@app.route('/unanswered_questions', methods=['POST'])
def save_unanswered():
    """Save an unanswered question for later review"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        question = data.get('question', '').strip()
        if not question:
            return jsonify({'error': 'No question provided'}), 400

        conn = get_db_connection()
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

@app.route('/student_feedback_counts', methods=['POST'])
def add_feedback_count():
    data = request.get_json()
    
    # Accept the full structure
    course = data.get('course')
    stanine = data.get('stanine')
    gwa = data.get('gwa')
    strand = data.get('strand')
    rating = data.get('rating')  # "like", "dislike", "neutral"
    hobbies = data.get('hobbies')
    count = data.get('count', 1)

    if not all([course, stanine, gwa, strand, rating, hobbies]):
        return jsonify({'error': 'Missing required fields'}), 400

    return jsonify({'status': 'added', 'course': course, 'rating': rating})
    
# ====== 4️⃣ GET COURSES ======
@app.route('/courses', methods=['GET'])
def get_courses():
    """Fetch all courses"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM courses ORDER BY course_name ASC")
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({'courses': results}), 200

    except Exception as e:
        print(f"Error fetching courses: {e}")
        return jsonify({'error': 'Failed to fetch courses', 'details': str(e)}), 500

# ====== 🗑️ DELETE UNANSWERED QUESTION BY ID ======
@app.route('/unanswered_questions/<int:question_id>', methods=['DELETE'])
def delete_unanswered_question(question_id):
    """
    Delete a specific unanswered question by its ID.
    Example:
    DELETE /unanswered_questions/5
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM unanswered_questions WHERE id = %s", (question_id,))
        conn.commit()
        affected_rows = cursor.rowcount
        cursor.close()
        conn.close()

        if affected_rows == 0:
            return jsonify({'error': f'No question found with id {question_id}'}), 404

        return jsonify({
            'status': 'deleted',
            'id': question_id,
            'message': 'Unanswered question successfully deleted.'
        }), 200

    except Exception as e:
        print(f"Error deleting unanswered question: {e}")
        return jsonify({
            'error': 'Failed to delete question',
            'details': str(e)
        }), 500

# ====== 5️⃣ HEALTH CHECK ======
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

# ===== 🖥️ SIMPLE UI =====
@app.route('/')
def index():
    return render_template('index.html')

# ====== APP RUNNER ======
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)




