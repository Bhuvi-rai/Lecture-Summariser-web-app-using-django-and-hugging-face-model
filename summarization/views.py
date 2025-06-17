from django.shortcuts import render, redirect, get_object_or_404
from django.utils.html import format_html
from .forms import LectureUploadForm
from .models import DetailedNotes, Lecture

import os
import io
import re
import base64
import requests
from pdfminer.high_level import extract_text as extract_pdf_text
from docx import Document
from matplotlib import pyplot as plt

# Hugging Face API Setup
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
HUGGINGFACE_API_TOKEN = "YOUR_HUGGINGFACE_API_KEY"  # Replace with your API key

def upload_lecture(request):
    """Handle file upload, text extraction, and note summarization."""
    if request.method == 'POST':
        form = LectureUploadForm(request.POST, request.FILES)
        if form.is_valid():
            lecture = form.save()
            file_path = lecture.lecture_file.path
            file_extension = os.path.splitext(file_path)[1].lower()

            if file_extension not in ['.pdf', '.doc', '.docx', '.txt']:
                return render(request, 'lecture/upload.html', {
                    'form': form,
                    'error': 'Unsupported file type. Please upload .pdf, .doc, .docx, or .txt files.'
                })

            extracted_text = extract_text_from_file(file_path, file_extension)
            if not extracted_text:
                return render(request, 'lecture/upload.html', {
                    'form': form,
                    'error': 'No readable text found in the uploaded file.'
                })

            summary = summarize_text(extracted_text, length=request.POST.get('summaryLength'))
            DetailedNotes.objects.create(lecture=lecture, notes=summary)
            return redirect('notes', lecture_id=lecture.id)
    else:
        form = LectureUploadForm()

    return render(request, 'lecture/upload.html', {'form': form})

def view_notes(request, lecture_id):
    """View summarized notes for a lecture."""
    notes = get_object_or_404(DetailedNotes, lecture_id=lecture_id)
    return render(request, 'lecture/notes.html', {'summary_text': notes.notes})

def extract_text_from_file(file_path, extension):
    """Extract text content from different file formats."""
    try:
        if extension == '.pdf':
            return extract_pdf_text(file_path).strip()
        elif extension in ['.doc', '.docx']:
            doc = Document(file_path)
            return "\n".join(paragraph.text for paragraph in doc.paragraphs).strip()
        elif extension == '.txt':
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
    except Exception as e:
        print(f"❌ Error extracting text from {extension} file: {e}")
    return ""

def summarize_text(text, length):
    """Summarize text either using online API or fallback method."""
    summary = summarize_with_huggingface(text)
    if summary:
        print("✅ Hugging Face API successfully generated the summary.")
        return summary
    else:
        print("⚠️ Hugging Face API failed. Using fallback summarization.")
        return summarize_locally(text, length)

def summarize_with_huggingface(text):
    """Summarize using Hugging Face API."""
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}
    try:
        response = requests.post(HUGGINGFACE_API_URL, headers=headers, json={"inputs": text})
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and "summary_text" in result[0]:
                return result[0]["summary_text"]
            else:
                print("⚠️ Unexpected API response format:", result)
        else:
            print(f"❌ Hugging Face API error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ API request failed: {e}")
    return None

def summarize_locally(text, length):
    """Fallback summarization without using Spacy."""
    sentences = split_into_sentences(text)

    if length == 'short':
        return ' '.join(sentences[:10])
    elif length == 'medium':
        return ' '.join(sentences[:25])
    else:
        return generate_detailed_summary(text)

def split_into_sentences(text):
    """Simple sentence splitter."""
    text = re.sub(r'\s+', ' ', text.strip())
    sentences = re.split(r'(?<=[.!?]) +', text)
    return sentences

def generate_detailed_summary(text):
    """Generate a detailed formatted summary with headings, bullet points, tables and diagrams."""
    detailed_summary = "<strong>Detailed Summary:</strong><br>"
    sections = [s.strip() for s in re.split(r'\n\s*\d+\.|\n\n|\n\s*-\s*|Subheading:', text) if s.strip()]
    section_counter = 1

    for section in sections:
        sentences = split_into_sentences(section)
        if len(sentences) < 3:
            continue

        first_line = sentences[0]
        subheading = first_line[:50] if len(first_line) > 10 else f"Section {section_counter}"

        detailed_summary += f"<strong>{subheading}:</strong><br><ul>"
        for sentence in sentences[:5]:
            detailed_summary += f"<li>{sentence.strip()}</li>"
        detailed_summary += '</ul>'

        section_counter += 1

    # Add Key Concepts table
    detailed_summary += "<br><strong>Key Concepts:</strong><br><table border='1'><tr><th>Concept</th><th>Detail</th></tr>"
    for concept, detail in extract_key_concepts(text).items():
        detailed_summary += f"<tr><td>{concept}</td><td>{detail}</td></tr>"
    detailed_summary += "</table>"

    # Add a diagram
    diagram_url = generate_diagram(sections)
    if diagram_url:
        detailed_summary += f"<br><strong>Generated Diagram:</strong><br><img src='{diagram_url}' alt='Diagram'>"

    return format_html(detailed_summary)

def extract_key_concepts(text):
    """Extract potential key concepts based on capitalized words."""
    concepts = {}
    pattern = re.compile(r'\b[A-Z][a-z]*(?:\s[A-Z][a-z]*){0,3}')
    for match in pattern.finditer(text):
        concept = match.group()
        detail_start = text.find(concept) + len(concept)
        detail = text[detail_start:detail_start + 100].split('.')[0]
        concepts[concept] = detail.strip()
    return concepts

def generate_diagram(sections):
    """Generate a base64-encoded bar chart showing section lengths."""
    try:
        fig, ax = plt.subplots(figsize=(10, 5))
        section_lengths = [len(section) for section in sections]
        ax.barh(range(len(sections)), section_lengths, tick_label=[f"Section {i+1}" for i in range(len(sections))])
        ax.set_xlabel('Length')
        ax.set_title('Section Length Analysis')

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close()

        return f"data:image/png;base64,{image_base64}"
    except Exception as e:
        print(f"❌ Error generating diagram: {e}")
        return None
