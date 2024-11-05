import re
import textwrap
import os
import tkinter as tk
from tkinter import filedialog, messagebox

# 특정 줄을 제거하는 함수
def remove_lines(text):
    lines = text.splitlines()

    result = []
    skip = False
    for line in lines:
        if '본문 내용' in line or '원고 내용' in line or '추가 내용' in line or line.startswith('-'):
            skip = True
        if '$' in line or '==' in line:
            skip = False
        if not skip:
            result.append(line)
    return '\n'.join(result)


# 텍스트를 처리하고 제목과 태그 섹션을 유지하는 함수
def process_text_preserving_title_tags(file_path, unique_filename, max_line_length_comments=40, min_lines_body=2, max_lines_body=6, max_line_length_body=35):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # 가장 먼저 \n을 제거하는 작업 수행
    content = re.sub(r'\\n+', '\n', content)

    cleaned_text = remove_lines(content)
    content_lines = cleaned_text.splitlines()
    new_content = []
    inside_body = False
    inside_comments = False
    comment_number = 1
    preserve_title = True
    title_section_done = False
    preserve_tags = False

    def split_paragraphs(text, min_lines, max_lines, max_line_length):
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        paragraphs = []
        current_paragraph = []
        line_count = 0
        for sentence in sentences:
            wrapped_sentence = textwrap.wrap(sentence, width=max_line_length)
            current_paragraph.extend(wrapped_sentence)
            line_count += len(wrapped_sentence)
            if line_count >= min_lines and (line_count >= max_lines or sentence.endswith(('.', '!', '?'))):
                paragraphs.append('\n'.join(current_paragraph))
                current_paragraph = []
                line_count = 0
        if current_paragraph:
            paragraphs.append('\n'.join(current_paragraph))
        return '\n\n'.join(paragraphs)

    for line in content_lines:
        line = line.replace('"', ' ')
        
        if '#제목' in line:
            preserve_title = True
            inside_body = False
            inside_comments = False
            new_content.append(line)
            continue

        if preserve_title and not title_section_done:
            new_content.append(line)
            title_section_done = True
            preserve_title = False
            continue

        if '#본문' in line:
            inside_body = True
            inside_comments = False
            preserve_title = False
            preserve_tags = False
            new_content.append(line)
            continue

        if '#댓글' in line:
            inside_body = False
            inside_comments = True
            preserve_title = False
            preserve_tags = False
            new_content.append(line)
            continue

        if '#태그' in line:
            preserve_tags = True
            new_content.append(line)
            inside_body = False
            inside_comments = False
            preserve_title = False
            continue

        if preserve_title or preserve_tags:
            new_content.append(line)
            continue

        if inside_body:
            if '사진:' in line:
                new_content.append(f'(사진{comment_number})')
                comment_number += 1
            else:
                paragraphs = split_paragraphs(line, min_lines_body, max_lines_body, max_line_length_body)
                new_content.append(paragraphs)

        elif inside_comments:
            paragraphs = split_paragraphs(line, min_lines_body, max_lines_body, max_line_length_comments)
            new_content.append(paragraphs)
            
    updated_file_path = os.path.join(os.getcwd(), unique_filename)
    with open(updated_file_path, 'w', encoding='utf-8') as file:
        for line in new_content:
            if isinstance(line, list):
                line = '\n'.join(line)
            if line.strip():
                file.write(line + '\n')

    return updated_file_path

# 고유한 파일 이름을 만드는 함수
def get_unique_filename(directory, filename):
    base, extension = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    while os.path.exists(os.path.join(directory, new_filename)):
        new_filename = f"{base}_{counter}{extension}"
        counter += 1
    return new_filename

# 여러 파일 선택을 위한 Tkinter GUI 코드
def browse_files():
    file_paths = filedialog.askopenfilenames()
    if file_paths:
        file_entry.delete(0, tk.END)
        file_entry.insert(0, ', '.join(file_paths))  # 선택된 파일들을 보여주기 위해

def process_files():
    file_paths = file_entry.get().split(', ')
    if not file_paths or file_paths[0] == '':
        messagebox.showerror("Error", "파일을 선택해주세요.")
        return

    result_message = ""
    max_files_per_prompt = 20  # 한 prompt 창에 표시할 최대 파일 수
    file_count = 0
    total_files = len(file_paths)
    
    for file_path in file_paths:
        filename = os.path.basename(file_path)
        directory = os.path.dirname(file_path)
        unique_filename = get_unique_filename(directory, filename)

        updated_file_path = process_text_preserving_title_tags(file_path, unique_filename)
        result_message += f"{updated_file_path}\n"  # 처리된 파일 경로 추가
        file_count += 1

        # 20개의 파일이 처리되면 메시지 박스 출력
        if file_count % max_files_per_prompt == 0:
            messagebox.showinfo("Success", f"파일 처리 완료! (총 {total_files}개 중 {file_count}개 처리)\n저장된 파일들:\n{result_message}")
            result_message = ""  # 메시지 리셋

    # 남은 파일 처리 (20개로 딱 나누어 떨어지지 않을 경우 마지막 메시지)
    if result_message:
        messagebox.showinfo("Success", f"파일 처리 완료! (총 {total_files}개 중 {file_count}개 처리)\n저장된 파일들:\n{result_message}")

# GUI 창 생성
root = tk.Tk()
root.title("원고 파일 교정프로그램")

# GUI 위젯 구성
file_label = tk.Label(root, text="파일 선택(.txt):")
file_label.grid(row=0, column=0, padx=10, pady=10)

file_entry = tk.Entry(root, width=50)
file_entry.grid(row=0, column=1, padx=10, pady=10)

browse_button = tk.Button(root, text="파일 찾기", command=browse_files)
browse_button.grid(row=0, column=2, padx=10, pady=10)

process_button = tk.Button(root, text="생성하기", command=process_files)
process_button.grid(row=1, column=1, padx=10, pady=10)

# GUI 실행
root.mainloop()
