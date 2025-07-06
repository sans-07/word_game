# 라이브러리와 모듈
import os
import random
from flask import Flask, render_template, request, session, redirect, url_for
from word_list import WORD_LIST

# Flask 애플리케이션을 생성
app = Flask(__name__)
# 세션 데이터를 암호화하기 위한 시크릿 키를 설정
# 환경 변수에서 SECRET_KEY를 가져오고, 없으면 개발용 기본값을 사용
app.secret_key = os.environ.get('SECRET_KEY', 'a-super-secret-key-for-development')

def start_new_game():
    """새 게임을 위한 세션 변수를 초기화"""
    session['target_word'] = random.choice(WORD_LIST)
    session['revealed_indices'] = []

# 메인 페이지 라우트 GET과 POST 요청을 모두 처리
@app.route("/", methods=["GET", "POST"])
def index():
    # 세션에 게임 상태가 없으면 새 게임을 시작
    if 'target_word' not in session:
        start_new_game()

    message = ""
    feedback = []
    guess = ""

    # 사용자가 단어를 제출했을 때 (POST 요청)
    if request.method == "POST":
        guess = request.form.get("word", "").lower()
        target_word = session['target_word']

        if len(guess) != len(target_word):
            message = f"{len(target_word)}글자 단어를 입력해야 합니다."
        elif guess == target_word:
            message = "정답입니다!"
            feedback = get_feedback_classes(guess, target_word)
            start_new_game() # 정답을 맞추면 새 게임 시작
        else:
            message = "다시 시도해보세요."
            feedback = get_feedback_classes(guess, target_word)
    
    # 힌트 표시를 위한 문자열을 생성
    target = session['target_word']
    revealed = session.get('revealed_indices', [])
    hint_display = " ".join([target[i] if i in revealed else "_" for i in range(len(target))])

    # index.html 템플릿을 렌더링하고, 필요한 데이터들을 전달
    return render_template(
        "index.html", 
        message=message, 
        guess=guess, 
        feedback=feedback, 
        word_length=len(target), 
        hint_display=hint_display
    )

# 힌트 제공 라우트
@app.route("/hint")
def hint():
    if 'target_word' in session:
        target = session['target_word']
        revealed = session.get('revealed_indices', [])
        
        unrevealed_indices = [i for i in range(len(target)) if i not in revealed]
        
        if unrevealed_indices:
            hint_index = random.choice(unrevealed_indices)
            session.setdefault('revealed_indices', []).append(hint_index)
            session.modified = True

    return redirect(url_for('index'))

# 게임 리셋 라우트
@app.route("/reset")
def reset():
    """세션을 초기화하여 새 게임을 시작"""
    start_new_game()
    return redirect(url_for('index'))

# 제출된 단어와 정답을 비교하여 피드백 클래스를 생성하는 함수
def get_feedback_classes(guess, answer):
    """
    Guess와 Answer를 비교하여 Wordle과 유사한 피드백 클래스를 생성
    - correct: 글자와 위치가 모두 정답
    - present: 글자는 정답에 있으나 위치가 다름
    - absent: 글자가 정답에 없음
    """
    guess_len = len(guess)
    answer_len = len(answer)
    feedback = [('absent', guess[i]) for i in range(guess_len)]
    
    answer_letter_counts = {}
    for letter in answer:
        answer_letter_counts[letter] = answer_letter_counts.get(letter, 0) + 1

    # 1. 'correct' (정확한 위치) 상태를 먼저 확인
    for i in range(min(guess_len, answer_len)):
        if guess[i] == answer[i]:
            feedback[i] = ('correct', guess[i])
            answer_letter_counts[guess[i]] -= 1

    # 2. 'present' (다른 위치에 존재) 상태를 확인
    for i in range(guess_len):
        if feedback[i][0] != 'correct':
            char = guess[i]
            if char in answer_letter_counts and answer_letter_counts[char] > 0:
                feedback[i] = ('present', char)
                answer_letter_counts[char] -= 1
    
    return feedback

# 이 스크립트가 직접 실행될 때 Flask 개발 서버를 시작
if __name__ == "__main__":
    app.run(debug=True)
