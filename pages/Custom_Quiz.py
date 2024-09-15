import streamlit as st
import os
import csv, time, math
from addtional_data import emojis, quirky_responses
from random import shuffle, choice
submitted=''

def reset_app():
    for key in st.session_state.keys():
        del st.session_state[key]

def reset():
    st.session_state.page = 'custom_quiz' 
    st.session_state.app_status = 'start'
    st.session_state.points = 0
    st.session_state.num_of_questions = '*'
    st.session_state.options = []
    st.session_state.current_q_no = 0
    st.session_state.quiz_data = []
    st.session_state.quiz_status = False

def check_answer(selected_answer, data):
    if(selected_answer  == data[f"option_{data['answer'].lower()}"]):
        return True
    else: 
        return False
    
def submit_quiz_answer(quiz_data,qno):
    if st.session_state.selected_answer_choice and not st.session_state.quiz_status:
        if check_answer(st.session_state.selected_answer_choice,quiz_data[qno]):
            st.session_state.points = st.session_state.points+1
        st.session_state.quiz_status = True

if 'page' in st.session_state and st.session_state.page != 'custom_quiz':
    reset()
    pass

if 'app_status' not in st.session_state:
    reset() 

def start_view():
    options = st.multiselect( "Select The topics you want quiz in", options = [file[:-4] for file in os.listdir('output')], key = 'options')
    st.text('Number of Questions You Want?')
    _, col1,  col2 = st.columns([.2,1,3.5])
    checked = col1.checkbox('All Question', True)
    
    if not checked:
        col2.number_input('Enter Number of Questions', step=1, min_value=5, value=5, key='num_of_questions')
    submitted = st.button('Submit')
    if submitted:
        if len(options) == 0:
            st.error('You Should select a topic!')
        else :
            st.session_state.quiz_topics = options
            if checked or 'num_of_questions' not in st.session_state : 
                st.session_state.num_of_questions = '*'
            st.session_state.app_status='q_prep'
            st.rerun()

def quiz_prep_view():
    with st.spinner('Generating Questions... Please wait..'):
        quiz_data = []
        for topic in st.session_state.options:
            count = st.session_state.num_of_questions
            limit = None if count == '*'  else count
            data =[]
            with open(f"output/{topic}.csv", mode='r') as file:
                reader = csv.DictReader(file, quotechar='"', delimiter=',')
                # Iterate over each row in the CSV file
                for row in reader:
                    data.append(row)
            shuffle(data)
            data=data[:limit or len(data)]
            quiz_data = quiz_data + data
        time.sleep(1)
        shuffle(quiz_data)
        st.session_state.quiz_data = quiz_data
        st.session_state.app_status='quiz'
        st.rerun()

def quiz_view():
    if st.session_state.current_q_no+1 > len(st.session_state.quiz_data):
        st.session_state.app_status = 'end'
        st.rerun()
    with st.form('aws_quiz'+str(st.session_state.current_q_no)):
        qno = st.session_state.current_q_no
        quiz_data = st.session_state.quiz_data
        st.caption(f"Question : {st.session_state.current_q_no+1}", help=f"Question {st.session_state.current_q_no+1} of {len(quiz_data)}")
        selected_option = st.radio(
            quiz_data[qno]['question'], 
            options=[quiz_data[qno]['option_a'], quiz_data[qno]['option_b'], quiz_data[qno]['option_c'], quiz_data[qno]['option_d']], 
            index=None, key='selected_answer_choice', disabled=st.session_state.quiz_status)
        form_submitted = st.form_submit_button(use_container_width = True, on_click=submit_quiz_answer, args=(quiz_data,qno))
    
    if form_submitted:
        if not selected_option:
            st.warning('Please select an option')
        else:
            st.button('Next Question',key='next_question')
            if check_answer(selected_option,quiz_data[qno]):
                st.success("Correct!")
            else:
                st.error(f"Wrong! The correct option is Option {quiz_data[qno]['answer']}")
            
            with st.expander('Explanation',icon='📖', expanded=True):
                    st.write(quiz_data[qno]['explanation'])

    if 'next_question' in st.session_state and st.session_state.next_question: 
        st.session_state.current_q_no = st.session_state.current_q_no+1
        st.session_state.quiz_status = False
        st.rerun()

def end_view():
    st.title('Quiz Completed! :balloon:')
    st.balloons()
    correct, total = st.session_state.points,st.session_state.current_q_no
    ind = max(math.ceil((correct/total)*10)-1,0)
    st.header(f'You Scored :blue[{correct}/{total}] {emojis[ind]}')
    st.caption(choice(quirky_responses[ind]))
    st.button('Reset',on_click=reset_app)


def main():
    # with st.sidebar:
    #     st.title('Quiz APP')

    c1, c2 = st.columns([2,1])
    c1.title('AWS Quiz APP')
    if st.session_state.app_status != 'start':
        c2.title(f':red[_Score_] : :blue[{str(st.session_state.points)}]', anchor=False)

    if st.session_state.app_status == 'start':
       start_view()
    
    if st.session_state.app_status == 'q_prep':
        quiz_prep_view()
    
    if st.session_state.app_status == 'quiz':
        quiz_view()
    
    if st.session_state.app_status == 'end':
        end_view()

if __name__ == '__main__': 
    try:
        main()
    except Exception as err:
        st.exception(err)
