import json,re
import logging
import time
import google.generativeai as genai
import config
from utilities.utility import extract_json
genai.configure(api_key=config.api_key)

FILE_NAME = 'SQS'

# Configure the logger
logging.basicConfig(
    filename="app.log",  # Name of the log file
    level=logging.INFO,  # Set the logging level
    format="%(asctime)s %(levelname)-8s %(message)s",  # Log format
    datefmt='%Y-%m-%d %H:%M'
)

# Create a logger object
logger = logging.getLogger(__name__)


lines = ''
with open(f'Input_Questions\{FILE_NAME}.txt','r', encoding='utf-8') as f:
    lines = f.readlines()

questions_and_answers = ' '.join(lines).split('Question:')

final_que_and_ans = []
for q_a in questions_and_answers:
    arrays = q_a.split('Answer:')
    if len(arrays[0].strip()) == 0 or len(arrays[1].strip()) == 0 :
        continue
    question = arrays[0].strip()
    answer = arrays[1].strip()
    final_que_and_ans.append((question,answer))



model = genai.GenerativeModel('gemini-1.5-flash', system_instruction='''
Instructions: 
You Should only respond with in JSON FORMAT no formating only json text
For the provided question and answer, create 3 additional multiple choice options that are closely related to the actual answer, as if they were options in a real test. 
If appropriate, include an "All of the above" or "None of the above" option as well.
One of the choices should include the correct answer, either verbatim or rephrased.
After the 4 options, include a single letter that indicates which option is the correct answer. 
Response should be in JSON format it should contain a key called "options" which is an array and should contain the 4 options and another key called "answer" that stores the alphabet of the correct answer
Context: The questions and answers are related to the AWS Developer certification exam.
''')


def validate_response(json_data)->bool:
    if json_data is None and json_data or len(json_data)<=0:
        logger.info('Failed due to null or zero len')
        return False
    if 'options' not in json_data[0]  :
        logger.info('Failed due to options key not present')
        return False
    if len(json_data[0]['options']) != 4:
        logger.info('Failed due to number of choise' +str(len(json_data[0]['options'])))
        return False
    if 'answer' not in json_data[0]:
        logger.info('Failed due to answer key not present')
        return False
    if json_data[0]['answer'].upper() not in ['A','B','C','D']:
        logger.info('Failed due to answer alphabet wrong')
        return False
    
    return True 

def ask_model(q_and_a):
    response = model.generate_content(f'''
        Question: {q_and_a[0]}
        Answer: {q_and_a[1]}
    ''')
    return response.text

start_time = int(time.time())

def check_time(count): 
    global start_time
    if count % 15 == 0:
        if int(time.time()) - start_time <60  :
            val = int(time.time()) - start_time
            print(f"waiting for {62 - val} sec to avoid rate limit")
            time.sleep(62 - val)
            start_time = int(time.time()) 
            pass 

count = 0
formated_q_and_a = [] 
for q_and_a in final_que_and_ans:
    attempt = 1
    json_data = None
    while attempt<3: 
        text = ask_model(q_and_a)
        count = count +1 
        check_time(count)
        json_data = extract_json(text)
        if validate_response(json_data):
            break
        else:
            json_data = None
            print('Invalid Response')
            logger.info(f"Invalid Response attempt {attempt} : "+text)
        attempt=attempt+1
    if not json_data:
        print('Skipping due to error')
    else:
        formated_q_and_a.append([q_and_a[0], *json_data[0]['options'], json_data[0]['answer'].upper(), q_and_a[1]])
        print(f"processed {count}")
    
print('Done')


header = ['question', 'option_a', 'option_b', 'option_c', 'option_d', 'answer', 'explanation']
formated_q_and_a[0], len(formated_q_and_a[0]), header, len(header)



import csv
with open(f"output/{FILE_NAME}.csv", "w", newline="") as csvfile:
    writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
    writer.writerows([header]+formated_q_and_a)