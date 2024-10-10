from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
from google.auth.transport.requests import Request
from openai import OpenAI
import json

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/tasks']

def get_credentials():
    creds = None
    # The file token.json stores the user's access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return creds

def get_service():
    creds = get_credentials()
    service = build('tasks', 'v1', credentials=creds)
    return service

def list_task_lists(service):
    try:
        results = service.tasklists().list().execute()
        items = results.get('items', [])
        if not items:
            print('No task lists found.')
        else:
            print('Task lists:')
            for item in items:
                print(f"{item['id']}: {item['title']}")
        return items
    except HttpError as error:
        print(f'An error occurred: {error}')

def list_all_tasks(service):
    try:
        task_lists = list_task_lists(service)
        all_tasks = []
        for task_list in task_lists:
            print(f"\nTasks in {task_list['title']}:")
            tasks = []
            page_token = None
            while True:
                results = service.tasks().list(tasklist=task_list['id'], pageToken=page_token).execute()
                tasks.extend(results.get('items', []))
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
            
            if not tasks:
                print('No tasks found in this list.')
            else:
                for task in tasks:
                    print(f"- {task['title']}")
                    all_tasks.append(task)
        return all_tasks
    except HttpError as error:
        print(f'An error occurred: {error}')

def cache_categorized_tasks(tasks, questions):
    cache = []
    for task, question in zip(tasks, questions):
        cache.append({
            'task_id': task['id'],
            'title': task['title'],
            'rephrased_question': question.split('. ', 1)[-1]  # Remove numbering
        })
    
    with open('task_cache.json', 'w') as f:
        json.dump(cache, f)

def load_cached_tasks():
    if os.path.exists('task_cache.json'):
        with open('task_cache.json', 'r') as f:
            return json.load(f)
    return None

def identify_questions(tasks):
    cached_tasks = load_cached_tasks()
    if cached_tasks:
        print("Using cached task categorization.")
        return cached_tasks

    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    prompt = "Identify which of the following tasks are questions. Rephrase them more properly, with one question per line. If a task is not a question, respond with 'Not a question.' for that task. Absolutely don't number them. Maintain the original order:\n\n"
    for task in tasks:
        prompt += f"- {task['title']}\n"
    
    response = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": "You are an assistant that identifies questions from a list of tasks."},
            {"role": "user", "content": prompt}
        ]
    )
    categorized_tasks = []
    for task, rephrased_question in zip(tasks, response.choices[0].message.content.strip().split('\n')):
        categorized_tasks.append({
            'task_id': task['id'],
            'title': task['title'],
            'rephrased_question': rephrased_question.split('. ', 1)[-1]  # Remove numbering
        })

    cache_categorized_tasks(tasks, response.choices[0].message.content.strip().split('\n'))
    return categorized_tasks

def get_llm_answer(messages):
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    response = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=messages
    )
    return response.choices[0].message.content.strip()

def get_task_list_id(service, task_id):
    tasklists_result = service.tasklists().list().execute()
    tasklists = tasklists_result.get('items', [])

    for tasklist in tasklists:
        tasklist_id = tasklist['id']
        tasks_result = service.tasks().list(tasklist=tasklist_id).execute()
        tasks = tasks_result.get('items', [])
        
        if any(task['id'] == task_id for task in tasks):
            return tasklist_id
    
    return None

def handle_question(service, task):
    print(f"Original task: {task['title']}")
    print(f"Rephrased question: {task['rephrased_question']}")
    
    if task['rephrased_question'].lower() == 'not a question.':
        print("This task is not a question. Skipping.")
        return

    messages = [
        {"role": "system", "content": "You are an assistant that provides accurate answers to questions."},
        {"role": "user", "content": f"Original question: {task['title']}\nRephrased question: {task['rephrased_question']}"}
    ]
    
    while True:
        user_input = input("Do you want an LLM answer for this question? (y/n): ").lower()
        if user_input in ['y', 'yes']:
            answer = get_llm_answer(messages + [{"role": "user", "content": "Please provide a medium-length, precise, and correct answer for the question above."}])
            print(f"\nA: {answer}\n")
            messages.append({"role": "assistant", "content": answer})
            
            while True:
                follow_up = input("Enter a follow-up question (or 'y' if satisfied, 'n' to skip): ").strip()
                if follow_up.lower() == 'y':
                    task_list_id = get_task_list_id(service, task['id'])
                    if task_list_id:
                        mark_task_complete(service, task_list_id, task['id'])
                        print("Task marked as complete.")
                    else:
                        print("Unable to mark task as complete: task list ID not found.")
                    return
                elif follow_up.lower() == 'n':
                    return
                else:
                    messages.append({"role": "user", "content": follow_up})
                    answer = get_llm_answer(messages)
                    print(f"\nA: {answer}\n")
                    messages.append({"role": "assistant", "content": answer})
        elif user_input in ['n', 'no']:
            return
        else:
            print("Invalid input. Please enter 'y' or 'n'.")

def mark_task_complete(service, task_list_id, task_id):
    print(f"Task ID: {task_id}")
    print(f"Task List ID: {task_list_id}")
    service.tasks().update(tasklist=task_list_id, task=task_id, body={'status': 'completed'}).execute()

def main():
    service = get_service()
    
    all_tasks = list_all_tasks(service)
    
    categorized_tasks = identify_questions(all_tasks)
    
    for task in categorized_tasks:
        handle_question(service, task)
        print()

if __name__ == '__main__':
    main()
