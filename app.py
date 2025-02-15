# app.py
from flask import Flask, render_template, request, session, redirect, url_for, make_response 
import groq
import re

app = Flask(__name__)
app.secret_key = 'your-secret-key-123'  # Change for production
app.static_folder = 'static'

# Initialize Groq Client
groq_client = groq.Client(api_key="YOUR_API_KEY")

def generate_mcq(category, difficulty, num_questions):
    prompt = f"""SYSTEM ROLE: You are a strict multiple-choice question generator with exceptional technical accuracy. 
    Generate EXACTLY {num_questions} unique MCQs combining {category} (ONLY: aptitude/reasoning/logic/code) with {difficulty} difficulty.

    FORMAT TEMPLATE - REPEAT THIS STRUCTURE {num_questions} TIMES:
    ---
    [NUMBER]. [Question stem CLEARLY requiring single correct answer]?
    a) [Distinct option 1]
    b) [Plausible option 2]
    c) [Best answer]
    d) [Common misconception]
    Answer: [LOWERCASE LETTER a-d]

    RULES:
    1. STRICT FORMAT: No variations in numbering, spacing, or punctuation
    2. ANSWER VALIDATION: Exactly 1 correct answer per question
    3. DISTRACTORS: Wrong answers must be plausible for the difficulty
    4. CATEGORY ADHERENCE: Technical accuracy for {category} domain
    5. OUTPUT CONTROL: No explanations, markdown, or extra text
    6. ERROR PREVENTION: If unsure about any question, regenerate it"""

    response = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are an expert MCQ generator for technical assessments."},
            {"role": "user", "content": prompt}
        ],
        model="llama3-70b-8192",
        temperature=0.3,
        max_tokens=4096,
        top_p=0.9,
        frequency_penalty=0.5,
        presence_penalty=0.5,
    )
    return response.choices[0].message.content

def parse_questions(text):
    questions = []
    pattern = r"(\d+)\.\s*(.*?)\?\s*a\)\s*(.*?)\s*b\)\s*(.*?)\s*c\)\s*(.*?)\s*d\)\s*(.*?)\s*Answer:\s*([a-d])"
    matches = re.findall(pattern, text, re.DOTALL)

    for match in matches:
        question_text = match[1].strip()
        options = [opt.strip() for opt in match[2:6]]
        correct_answer = match[6].strip().lower()

        questions.append({
            "question": question_text,
            "options": options,
            "answer": correct_answer
        })

    return questions

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        session.clear()
        session['category'] = request.form['category']
        session['difficulty'] = request.form['difficulty']
        session['num_questions'] = int(request.form['num_questions'])
        return redirect(url_for('generate_test'))
    return render_template('index.html')

@app.route('/generate-test')
def generate_test():
    test_content = generate_mcq(
        session['category'],
        session['difficulty'],
        session['num_questions']
    )
    session['questions'] = parse_questions(test_content)
    session['current_question'] = 0
    session['answers'] = {}
    session['submitted'] = False
    return redirect(url_for('show_question'))

@app.route('/question', methods=['GET', 'POST'])
def show_question():
    if request.method == 'POST':
        current_q = session['current_question']
        current_q_str = str(current_q)

        if 'answer' in request.form:
            session['answers'][current_q_str] = request.form.get('answer')

        if 'prev' in request.form:
            session['current_question'] = max(0, current_q - 1)
        elif 'next' in request.form:
            session['current_question'] = min(len(session['questions']) - 1, current_q + 1)
        elif 'submit' in request.form:
            session['submitted'] = True
            return redirect(url_for('show_results'))

        return redirect(url_for('show_question'))

    if session['submitted'] or not session.get('questions'):
        return redirect(url_for('index'))

    current_question_index = session['current_question']
    question = session['questions'][current_question_index]
    total_questions = len(session['questions'])

    return render_template(
        'question.html',
        question=question,
        question_num=current_question_index + 1,
        total_questions=total_questions,
        answers=session['answers'],
        current_question=current_question_index,
    )

@app.route('/results')
def show_results():
    if not session.get('submitted'):
        return redirect(url_for('index'))

    score = 0
    results = []
    missed_questions = []

    for i in range(len(session['questions'])):
        question = session['questions'][i]
        user_answer = session['answers'].get(str(i), "No answer")
        correct_letter = question['answer'].lower()
        is_correct = user_answer and user_answer[0].lower() == correct_letter

        if is_correct:
            score += 1
        else:
            missed_questions.append({
                'number': i + 1,
                'question': question['question']
            })

        results.append({
            'question': question['question'],
            'user_answer': user_answer,
            'correct_answer': f"{correct_letter}) {question['options'][ord(correct_letter) - ord('a')]}",
            'is_correct': is_correct
        })

    return render_template(
        'results.html',
        score=score,
        total=len(session['questions']),
        results=results,
        missed_questions=missed_questions
    )

# New download route
@app.route('/download-questions')
def download_questions():
    if not session.get('submitted'):
        return redirect(url_for('index'))
    
    import json
    from datetime import datetime
    
    # Create filename based on test parameters and current time
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{session['category']}-{session['difficulty']}-{session['num_questions']}-{timestamp}.json"
    
    # Prepare JSON data structure
    json_data = {
        'test_info': {
            'category': session['category'],
            'difficulty': session['difficulty'],
            'num_questions': session['num_questions'],
            'timestamp': timestamp
        },
        'questions': []
    }
    
    # Add each question with its details
    for i, question in enumerate(session['questions']):
        question_data = {
            'question_number': i + 1,
            'question_text': question['question'],
            'options': {
                'a': question['options'][0],
                'b': question['options'][1],
                'c': question['options'][2],
                'd': question['options'][3]
            },
            'correct_answer': question['answer'],
            'user_answer': session['answers'].get(str(i), "Not answered")
        }
        json_data['questions'].append(question_data)
    
    # Create the response with JSON data
    response = make_response(json.dumps(json_data, indent=2))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    
    return response

if __name__ == '__main__':
    app.run(debug=True)
