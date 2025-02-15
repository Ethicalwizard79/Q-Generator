from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import groq
import re
import uuid

app = FastAPI()

# Initialize Groq Client
groq_client = groq.Client(api_key="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")

# (Include the same generate_mcq and parse_questions functions from the Flask app here)

class TestRequest(BaseModel):
    category: str
    difficulty: str
    num_questions: int

class QuestionResponse(BaseModel):
    id: str
    question: str
    options: List[str]

class TestResponse(BaseModel):
    test_id: str
    questions: List[QuestionResponse]

class AnswerSubmission(BaseModel):
    test_id: str
    answers: Dict[int, str]

class TestResult(BaseModel):
    score: int
    total: int
    results: List[Dict]

api_tests = {}

@app.post("/create-test", response_model=TestResponse)
async def create_test(request: TestRequest):
    test_content = generate_mcq(
        request.category,
        request.difficulty,
        request.num_questions
    )
    questions = parse_questions(test_content)
    test_id = str(uuid.uuid4())
    
    api_tests[test_id] = {
        'questions': questions,
        'answers': {i: q['answer'] for i, q in enumerate(questions)}
    }
    
    return {
        'test_id': test_id,
        'questions': [
            {
                'id': str(uuid.uuid4()),
                'question': q['question'],
                'options': q['options']
            }
            for q in questions
        ]
    }

@app.post("/submit-test", response_model=TestResult)
async def submit_test(submission: AnswerSubmission):
    if submission.test_id not in api_tests:
        raise HTTPException(status_code=404, detail="Test not found")
    
    test = api_tests[submission.test_id]
    score = 0
    results = []
    
    for i, q in enumerate(test['questions']):
        correct_answer = test['answers'][i]
        user_answer = submission.answers.get(i, '').lower()
        is_correct = user_answer == correct_answer
        
        if is_correct:
            score += 1
        
        results.append({
            'question': q['question'],
            'user_answer': user_answer,
            'correct_answer': correct_answer,
            'is_correct': is_correct
        })
    
    return {
        'score': score,
        'total': len(test['questions']),
        'results': results
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)