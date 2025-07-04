# 필요한 라이브러리와 모듈을 가져옵니다.
from flask import Flask, render_template, request, session, redirect, url_for
import random
from word_list import WORD_LIST

# Flask 애플리케이션을 생성합니다.
app = Flask(__name__)
# 세션 데이터를 암호화하기 위한 시크릿 키를 설정합니다.
app.secret_key = 'supersecretkey'

# 메인 페이지 라우트입니다. GET과 POST 요청을 모두 처리합니다.
@app.route("/", methods=["GET", "POST"])
def index():
    # 세션에 정답 단어가 없으면, 새로운 단어를 선택하고 힌트 상태를 초기화합니다.
    if 'target_word' not in session:
        session['target_word'] = random.choice(WORD_LIST)
        session['revealed_indices'] = []

    # 템플릿에 전달할 변수들을 초기화합니다.
    message = ""
    guess = ""
    feedback = []
    hint_display = ""

    # 사용자가 단어를 제출했을 때 (POST 요청)
    if request.method == "POST":
        # 폼에서 제출된 단어를 가져와 소문자로 변환합니다.
        guess = request.form.get("word", "").lower()
        target_word = session['target_word']

        # 제출된 단어의 길이가 정답 단어와 다를 경우 메시지를 설정합니다.
        if len(guess) != len(target_word):
            message = f"⚠️ {len(target_word)}글자 단어를 입력해야 합니다."
        # 정답을 맞췄을 경우
        elif guess == target_word:
            message = "🎉 정답입니다!"
            feedback = get_feedback_classes(guess, target_word)
            # 세션에서 정답 단어와 힌트 정보를 제거하여 게임을 리셋합니다.
            session.pop('target_word', None)
            session.pop('revealed_indices', None)
        # 오답일 경우
        else:
            message = "🤔 다시 시도해보세요."
            feedback = get_feedback_classes(guess, target_word)
            
    # 현재 게임 상태에 대한 정보를 설정합니다.
    word_length_hint = 0
    if 'target_word' in session:
        target = session['target_word']
        revealed = session.get('revealed_indices', [])
        word_length_hint = len(target)
        # 힌트로 공개된 글자를 보여주고, 나머지는 밑줄로 표시합니다.
        hint_display = " ".join([target[i] if i in revealed else "_" for i in range(len(target))])

    # index.html 템플릿을 렌더링하고, 필요한 데이터들을 전달합니다.
    return render_template("index.html", message=message, guess=guess, feedback=feedback, word_length=word_length_hint, hint_display=hint_display)

# 힌트 제공 라우트입니다.
@app.route("/hint")
def hint():
    # 정답 단어가 세션에 있을 경우에만 힌트를 제공합니다.
    if 'target_word' in session:
        target = session['target_word']
        revealed = session.get('revealed_indices', [])
        
        # 아직 공개되지 않은 글자들의 인덱스를 찾습니다.
        unrevealed_indices = [i for i in range(len(target)) if i not in revealed]
        
        # 공개할 글자가 남아있다면, 랜덤으로 하나를 선택하여 공개합니다.
        if unrevealed_indices:
            hint_index = random.choice(unrevealed_indices)
            session.setdefault('revealed_indices', []).append(hint_index)
            session.modified = True  # 세션이 변경되었음을 명시적으로 알립니다.

    # 메인 페이지로 리디렉션합니다.
    return redirect(url_for('index'))

# 게임 리셋 라우트입니다.
@app.route("/reset")
def reset():
    # 세션에서 정답 단어와 힌트 정보를 제거합니다.
    session.pop('target_word', None)
    session.pop('revealed_indices', None)
    # 메인 페이지로 리디렉션하여 새 게임을 시작합니다.
    return redirect(url_for('index'))

# 제출된 단어와 정답을 비교하여 피드백 클래스를 생성하는 함수입니다.
def get_feedback_classes(guess, answer):
    """
    Guess와 Answer를 비교하여 Wordle과 유사한 피드백 클래스를 생성합니다.
    - correct: 글자와 위치가 모두 정답
    - present: 글자는 정답에 있으나 위치가 다름
    - absent: 글자가 정답에 없음
    """
    guess_len = len(guess)
    answer_len = len(answer)
    # 모든 글자를 기본적으로 'absent' (없음) 상태로 초기화합니다.
    feedback = [('absent', guess[i]) for i in range(guess_len)]
    
    # 정답 단어에 포함된 각 글자의 개수를 셉니다.
    answer_letter_counts = {}
    for letter in answer:
        answer_letter_counts[letter] = answer_letter_counts.get(letter, 0) + 1

    # 1. 'correct' (정확한 위치) 상태를 먼저 확인합니다.
    for i in range(min(guess_len, answer_len)):
        if guess[i] == answer[i]:
            feedback[i] = ('correct', guess[i])
            # 'correct'로 확인된 글자는 개수에서 제외합니다.
            answer_letter_counts[guess[i]] -= 1

    # 2. 'present' (다른 위치에 존재) 상태를 확인합니다.
    for i in range(guess_len):
        # 이미 'correct'로 판정된 글자는 건너뜁니다.
        if feedback[i][0] != 'correct':
            char = guess[i]
            # 해당 글자가 정답에 남아있는 경우 'present'로 설정합니다.
            if char in answer_letter_counts and answer_letter_counts[char] > 0:
                feedback[i] = ('present', char)
                answer_letter_counts[char] -= 1
    
    return feedback

# 이 스크립트가 직접 실행될 때 Flask 개발 서버를 시작합니다.
if __name__ == "__main__":
    app.run(debug=True)