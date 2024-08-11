import pandas as pd
import streamlit as st
import io
import random
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.backends.backend_agg as agg
from io import BytesIO
import matplotlib

def load_quiz_data(file):
    with io.TextIOWrapper(file, encoding='utf-8', errors='replace') as f:
        df = pd.read_csv(f)
    return df

def filter_quiz_data(df, selected_years, selected_categories):
    if "すべて" in selected_years:
        selected_years = df['year'].unique().tolist()
    if "すべて" in selected_categories:
        selected_categories = df['category'].unique().tolist()
    
    filtered_df = df[df['year'].isin(selected_years) & df['category'].isin(selected_categories)]
    
    quiz_data = []
    for _, row in filtered_df.iterrows():
        options = [row["option1"], row["option2"], row["option3"], row["option4"], row["option5"]]
        correct_option = row["answer"]
        shuffled_options = options[:]
        random.shuffle(shuffled_options)
        
        quiz_data.append({
            "question": row["question"],
            "options": shuffled_options,
            "correct_option": correct_option
        })
    return quiz_data

def save_table_as_image(df):
    # Set the Japanese font
    matplotlib.rcParams['font.family'] = 'MS Gothic'
    
    fig, ax = plt.subplots(figsize=(10, 2 + len(df) * 0.5))  # Adjust size based on the number of rows
    ax.axis('off')
    
    # Convert DataFrame to a table in the figure
    table = ax.table(cellText=df.values, colLabels=df.columns, cellLoc='center', loc='center', colColours=['#f5f5f5'] * len(df.columns))
    table.auto_set_font_size(False)
    table.set_fontsize(10)  # Match font size with other elements
    table.scale(1.2, 1.2)  # Adjust the scaling if needed
    
    # Save the image to a BytesIO buffer
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1)
    buf.seek(0)
    plt.close(fig)
    return buf

def main():
    st.title("国家試験対策アプリ")

    if "quiz_data" not in st.session_state:
        st.session_state.quiz_data = []
    if "incorrect_data" not in st.session_state:
        st.session_state.incorrect_data = []
    if "current_quiz_data" not in st.session_state:
        st.session_state.current_quiz_data = []
    if "answers" not in st.session_state:
        st.session_state.answers = {}
    if "shuffled_options" not in st.session_state:
        st.session_state.shuffled_options = {}
    if "highlighted_questions" not in st.session_state:
        st.session_state.highlighted_questions = set()
    if "submit_count" not in st.session_state:
        st.session_state.submit_count = 0

    if "completed_problems" not in st.session_state:
        st.session_state.completed_problems = []

    uploaded_file = st.file_uploader("問題データのCSVファイルをアップロードしてください", type="csv")
    if uploaded_file is not None:
        try:
            df = load_quiz_data(uploaded_file)
            years = df['year'].unique().tolist()
            categories = df['category'].unique().tolist()

            years.insert(0, "すべて")
            categories.insert(0, "すべて")

            selected_years = st.multiselect("過去問の回数を選択してください", years)
            selected_categories = st.multiselect("分野を選択してください", categories)

            if selected_years and selected_categories:
                st.session_state.quiz_data = filter_quiz_data(df, selected_years, selected_categories)
                st.session_state.current_quiz_data = st.session_state.quiz_data.copy()
                st.session_state.answers = {quiz["question"]: None for quiz in st.session_state.current_quiz_data}

            if st.session_state.current_quiz_data:
                for i, quiz in enumerate(st.session_state.current_quiz_data):
                    question_number = i + 1
                    is_highlighted = question_number in st.session_state.highlighted_questions
                    highlight_style = "background-color: #ffcccc;" if is_highlighted else ""

                    st.markdown(f"**<div style='padding: 10px; {highlight_style} font-size: 16px;'>問題 {question_number}</div>**", unsafe_allow_html=True)
                    st.markdown(f"<p style='margin-bottom: 0; font-size: 16px;'>{quiz['question']}</p>", unsafe_allow_html=True)

                    if quiz["question"] not in st.session_state.shuffled_options:
                        st.session_state.shuffled_options[quiz["question"]] = quiz["options"]
                    
                    options = st.session_state.shuffled_options[quiz["question"]]

                    selected_option = st.radio(
                        "",
                        options=options,
                        index=st.session_state.answers.get(quiz["question"], None),
                        key=f"question_{i}_radio"
                    )

                    if selected_option is not None:
                        st.session_state.answers[quiz["question"]] = selected_option

                    st.write("")  # 次の問題との間にスペースを追加

                if st.button("回答"):
                    score = 0
                    total_questions = len(st.session_state.quiz_data)
                    incorrect_data = []
                    for i, quiz in enumerate(st.session_state.current_quiz_data):
                        correct_option = quiz["correct_option"]
                        selected_option = st.session_state.answers.get(quiz["question"], None)

                        is_correct = correct_option == selected_option

                        if is_correct:
                            score += 1
                            st.session_state.highlighted_questions.discard(i + 1)
                        else:
                            incorrect_data.append(quiz)
                            st.session_state.highlighted_questions.add(i + 1)

                    accuracy_rate = (score / total_questions) * 100
                    st.write(f"あなたのスコア: {score} / {total_questions}")
                    st.write(f"正答率: {accuracy_rate:.2f}%")

                    if score == total_questions:
                        st.success(f"すべての問題に正解しました！")

                        completed_problem = {
                            "日付": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "過去問": ", ".join(selected_years),
                            "分野": ", ".join(selected_categories),
                            "問題数": total_questions
                        }
                        st.session_state.completed_problems.append(completed_problem)

                        st.markdown("<h3 style='font-size: 16px;'>完了した問題</h3>", unsafe_allow_html=True)
                        df_completed = pd.DataFrame(st.session_state.completed_problems)
                        st.write(df_completed)

                        # Convert the table to an image
                        image_buffer = save_table_as_image(df_completed)
                        st.download_button(
                            label="証明書をダウンロード",
                            data=image_buffer,
                            file_name="completed_problems.png",
                            mime="image/png"
                        )

                    st.session_state.current_quiz_data = incorrect_data.copy()
                    st.session_state.submit_count += 1

        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
