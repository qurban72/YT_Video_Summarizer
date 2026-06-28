# src/graph.py
from langgraph.graph import StateGraph, START, END
from state import GraphState
from nodes import extract_video_id, extract_transcript, generate_pdf_notes

builder = StateGraph(GraphState)

builder.add_node("extract_video_id", extract_video_id)
builder.add_node("extract_transcript", extract_transcript)
builder.add_node("generate_pdf_notes", generate_pdf_notes)

builder.add_edge(START, "extract_video_id")

def route_after_node(state: GraphState):
    return "end" if state.error_message else "continue"

builder.add_conditional_edges("extract_video_id", route_after_node, {"continue": "extract_transcript", "end": END})
builder.add_conditional_edges("extract_transcript", route_after_node, {"continue": "generate_pdf_notes", "end": END})

builder.add_edge("generate_pdf_notes", END)

study_agent_graph = builder.compile()
