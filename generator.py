import streamlit as st
import groq
import re

# Initialize Groq Client
api_key = "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"
client = groq.Client(api_key=api_key)

def generate_mcq(category, difficulty, num_questions):
    prompt = f"""Generate EXACTLY {num_questions} unique multiple-choice questions combining {category} (strictly: reasoning, logic, code, behavior) with EXACTLY {difficulty} difficulty (Easy/Medium/Hardest). 
    Format each question EXACTLY as follows:
    ---
    X. [Question text]?
    a) [Option 1]
    b) [Option 2]
    c) [Option 3]
    d) [Option 4]
    Answer: [Letter a-d]
    ---
    RULES:
    1. NO explanations, NO deviations, NO extra text.
    2. Questions MUST be unique and not reuse concepts.
    3. Answers MUST be single letters (a-d) and correspond to the correct option.
    4. Ensure the format is EXACTLY as specified above, with no extra spaces, characters, or deviations."""
    
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="mixtral-8x7b-32768",
        max_tokens=30000,
    )
    return response.choices[0].message.content.strip()

def parse_questions(text):
    questions = []
    # Regex pattern to strictly match the required format
    pattern = r"(\d+)\.\s*(.*?)\?\s*a\)\s*(.*?)\s*b\)\s*(.*?)\s*c\)\s*(.*?)\s*d\)\s*(.*?)\s*Answer:\s*([a-d])"
    matches = re.findall(pattern, text, re.DOTALL)
    
    for match in matches:
        # Extract and clean components
        question_text = match[1].strip()
        options = [opt.strip() for opt in match[2:6]]
        answer = match[6].strip().lower()
        
        # Validate the answer is a single letter (a-d)
        if answer not in ['a', 'b', 'c', 'd']:
            continue  # Skip invalid questions
        
        questions.append({
            "question": question_text,
            "options": options,
            "answer": answer
        })
    
    return questions

# Initialize session state
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'answers' not in st.session_state:
    st.session_state.answers = {}
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

# Sidebar controls
st.sidebar.header("Test Settings")
category = st.sidebar.selectbox("Category", ['Aptitude', 'Reasoning', 'Code', 'Mathematics'])
difficulty = st.sidebar.selectbox("Difficulty", ['Beginner-level', 'Mid-level', 'Hard-level'])
num_questions = st.sidebar.selectbox("Number of Questions", [10, 20, 30, 40])

if st.sidebar.button("Generate New Test"):
    test_content = generate_mcq(category, difficulty, num_questions)
    st.session_state.questions = parse_questions(test_content)
    st.session_state.current_question = 0
    st.session_state.answers = {}
    st.session_state.submitted = False

# Main test interface
st.title("Interactive MCQ Test")

if st.session_state.questions:
    if not st.session_state.submitted:
        # Display current question
        q = st.session_state.questions[st.session_state.current_question]
        st.subheader(f"Question {st.session_state.current_question + 1}")
        st.write(q['question'])
        
        # Store answer
        options = [f"{chr(97+i)}) {option}" for i, option in enumerate(q['options'])]
        
        # Get the selected answer for the current question from session state
        selected_option = st.session_state.answers.get(st.session_state.current_question, None)
        
        # Display the radio button and update the session state when an option is selected
        answer = st.radio(
            "Select your answer:",
            options,
            index=options.index(selected_option) if selected_option in options else None,
            key=f"question_{st.session_state.current_question}"  # Unique key for each question
        )
        
        # Update the session state with the selected answer
        if answer:
            st.session_state.answers[st.session_state.current_question] = answer
        
        # Navigation buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("Previous") and st.session_state.current_question > 0:
                st.session_state.current_question -= 1
                st.rerun()
        with col2:
            st.write(f"Question {st.session_state.current_question + 1} of {len(st.session_state.questions)}")
        with col3:
            if st.button("Next") and st.session_state.current_question < len(st.session_state.questions) - 1:
                st.session_state.current_question += 1
                st.rerun()
        
        # Submit button
        if st.button("Submit Test"):
            st.session_state.submitted = True
            # Finalize answers after submission
            for i, q in enumerate(st.session_state.questions):
                user_answer = st.session_state.answers.get(i, " ")
                correct = user_answer.lower() == q['answer'].lower()
                st.session_state.answers[i] = {"user_answer": user_answer, "correct_answer": q['answer'], "correct": correct}
            st.rerun()
    else:
        # Calculate score and show results after submission
        score = 0
        results = []
        for i, q in enumerate(st.session_state.questions):
            result = st.session_state.answers.get(i, {})
            user_answer = result.get('user_answer', " ")
            correct_answer = result.get('correct_answer', "")
            correct = result.get('correct', False)
            if correct:
                score += 1
            results.append({
                "question": q['question'],
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "correct": correct
            })
        
        # Display results
        st.subheader(f"Your Score: {score} out of {len(st.session_state.questions)}")
        
        with st.expander("Review Questions"):
            for i, result in enumerate(results):
                st.markdown(f"**Question {i+1}**: {result['question']}")
                st.markdown(f"Your answer: {result['user_answer']} | Correct answer: {result['correct_answer']}")
                st.markdown(f"**{'Correct' if result['correct'] else 'Incorrect'}**")
                st.divider()
        
        if st.button("Take New Test"):
            st.session_state.questions = []
            st.session_state.submitted = False
            st.rerun()
else:
    st.info("Select your test settings and click 'Generate New Test' to begin")