# src/nodes.py
import os
import requests
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from state import GraphState
from dotenv import load_dotenv
load_dotenv()
# Gemini Flash-Lite configuration with precise safety parameters
llm = ChatGoogleGenerativeAI(model='gemini-3.1-flash-lite', max_retries=3, temperature=0.3)

def extract_video_id(state: GraphState):
    url = state.video_url
    regex = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S+\?v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    match = re.search(regex, url)
    if match: return {"video_id": match.group(1)}
    return {"error_message": "Invalid YouTube URL!"}

def extract_transcript(state: GraphState):
    if state.error_message: return {}
    video_id = state.video_id
    rapidapi_key = os.getenv("RAPIDAPI_KEY")
    
    if not rapidapi_key: return {"error_message": "RapidAPI Key is missing in .env!"}
        
    url = "https://youtube-transcript3.p.rapidapi.com/api/transcript"
    headers = {
        "Content-Type": "application/json",
        "X-RapidAPI-Key": rapidapi_key.strip(),
        "X-RapidAPI-Host": "youtube-transcript3.p.rapidapi.com"
    }
    try:
        response = requests.get(url, headers=headers, params={"videoId": video_id}, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if "transcript" in data:
                transcript_data = data["transcript"]
                text = " ".join([s.get('text', '') for s in transcript_data]) if isinstance(transcript_data, list) else str(transcript_data)
                return {"transcript": text}
        return {"error_message": "Failed to fetch transcript. Check API limits."}
    except Exception as e:
        return {"error_message": str(e)}

def generate_pdf_notes(state: GraphState):
    if state.error_message: return {}
    
    template = PromptTemplate(
        template='''
        Analyze this YouTube transcript and generate comprehensive, well-structured study notes.
        Organize into sections with logical headings. Use clear bold text for important terminology and bullet points for lists.
        Do not use any markdown formatting except basic headers (###) and bolding (**text**).
        
        Transcript: {transcript}
        ''',
        input_variables=["transcript"]
    )
    
    try:
        # LLM Invocation
        chain = template | llm
        response = chain.invoke({"transcript": state.transcript})
        
        # --- Flash-Lite Safe String Casting Engine (Fixes 'expected str instance, int found') ---
        content = ""
        
        if isinstance(response, str):
            content = response
            
        elif hasattr(response, 'content'):
            if isinstance(response.content, list):
                # Har item ko explicitly str() me wrap karna zaroori hai sequence error se bachne k liye
                extracted_lines = []
                for item in response.content:
                    if isinstance(item, dict):
                        extracted_lines.append(str(item.get('text', '')))
                    else:
                        extracted_lines.append(str(item))
                content = "\n".join(extracted_lines)
            else:
                content = str(response.content)
                
        elif isinstance(response, list):
            extracted_chunks = []
            for item in response:
                if hasattr(item, 'content'):
                    extracted_chunks.append(str(item.content))
                elif isinstance(item, dict):
                    extracted_chunks.append(str(item.get('text', '')))
                else:
                    extracted_chunks.append(str(item)) # Converts int, float, or object safely
            content = "\n".join(extracted_chunks)
            
        else:
            content = str(response)

        content = content.strip()
        if not content:
            return {"error_message": "Gemini generated an empty text output."}

        # --- ReportLab PDF Generation Logic ---
        pdf_filename = f"notes_{state.video_id}.pdf"
        doc = SimpleDocTemplate(
            pdf_filename,
            pagesize=letter,
            rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54
        )
        
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'PDFTitle', parent=styles['Title'],
            fontName='Helvetica-Bold', fontSize=24, leading=28,
            textColor=colors.HexColor('#1E3A8A'), alignment=0, spaceAfter=15
        )
        h2_style = ParagraphStyle(
            'PDFH2', parent=styles['Heading2'],
            fontName='Helvetica-Bold', fontSize=14, leading=18,
            textColor=colors.HexColor('#2563EB'), spaceBefore=15, spaceAfter=8,
            keepWithNext=True
        )
        body_style = ParagraphStyle(
            'PDFBody', parent=styles['BodyText'],
            fontName='Helvetica', fontSize=10, leading=15,
            textColor=colors.HexColor('#374151'), spaceAfter=8
        )
        
        story = []
        
        story.append(Paragraph("📄 YouTube Video Study Companion Notes", title_style))
        story.append(Paragraph(f"<b>Source URL:</b> {state.video_url}", body_style))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E5E7EB'), spaceAfter=15))
        
        # Ab join string datatype strict validation pass ho chuki hai
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line: continue
            
            line = line.replace('**', '<b>', 1).replace('**', '</b>', 1)
            line = re.sub(r'^\*+\s*', '• ', line)
            
            if line.startswith('###') or line.startswith('##') or line.startswith('#'):
                clean_heading = line.replace('#', '').strip()
                story.append(Paragraph(clean_heading, h2_style))
            else:
                story.append(Paragraph(line, body_style))
                
        doc.build(story)
        return {"summary": content, "pdf_path": pdf_filename}
        
    except Exception as e:
        return {"error_message": f"Error generating study pack: {str(e)}"}
