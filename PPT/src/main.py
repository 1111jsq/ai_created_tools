import sys
import os
import argparse
from .llm_service import LLMService
from .ppt_renderer import PPTRenderer

def main():
    parser = argparse.ArgumentParser(description="Generate PPT charts from natural language.")
    parser.add_argument("input", help="Natural language text or path to a text file.")
    parser.add_argument("--output", "-o", default="output.pptx", help="Output PPTX filename.")
    parser.add_argument("--api-key", help="OpenAI API Key (optional if set in env).")
    parser.add_argument("--base-url", help="OpenAI Base URL (optional if set in env).")
    parser.add_argument("--style", choices=["tech", "light", "retro"], default="tech", help="Visual style of the PPT.")
    
    args = parser.parse_args()

    # Read input
    if os.path.exists(args.input):
        with open(args.input, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = args.input

    print(f"Analyzing input: {text[:50]}...")

    # Initialize Services
    try:
        llm = LLMService(api_key=args.api_key, base_url=args.base_url)
        renderer = PPTRenderer(style_name=args.style)
        
        # Process
        print("Querying LLM for structured data...")
        presentation_request = llm.analyze_data(text)
        print(f"Plan created: {presentation_request.chart_type} - {presentation_request.slide_title}")
        
        print("Generating PPT...")
        renderer.create_presentation(presentation_request, args.output)
        print("Done!")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

