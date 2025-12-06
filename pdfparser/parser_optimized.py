"""
Optimized PDF Parser for College Common Data Set Documents

This module extracts text from PDF files and uses OpenAI to extract
structured information about college admission requirements and statistics.
"""

import pdfplumber
from openai import OpenAI
import os
import json
from pathlib import Path
from typing import Optional
import sys


class PDFParser:
    """Optimized PDF parser with better error handling and resource management."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize the PDF parser.
        
        Args:
            api_key: OpenAI API key (defaults to environment variable OPENAI_API_KEY)
            model: OpenAI model to use (default: gpt-4o-mini)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not provided. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
    
    def extract_text_from_pdf(self, filename: str) -> str:
        """
        Extract text from a PDF file efficiently.
        
        Args:
            filename: Path to the PDF file
            
        Returns:
            Extracted text as a string
            
        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            ValueError: If the file is not a PDF
        """
        # Validate file exists
        if not os.path.exists(filename):
            raise FileNotFoundError(f"File not found: {filename}")
        
        # Validate file extension
        if not filename.lower().endswith('.pdf'):
            raise ValueError(f"File must be a PDF: {filename}")
        
        # Use list comprehension for better memory efficiency
        # This is more efficient than string concatenation in a loop
        try:
            with pdfplumber.open(filename) as pdf:
                # Extract text from all pages using list comprehension
                # This is more memory-efficient than string concatenation
                text_pages = [page.extract_text() or "" for page in pdf.pages]
                text = "\n".join(text_pages)
            
            if not text.strip():
                print(f"⚠️  Warning: No text extracted from {filename}")
            
            return text
        except Exception as e:
            raise RuntimeError(f"Error extracting text from PDF: {str(e)}") from e
    
    def save_extracted_text(self, text: str, output_path: str = "extracted_text.txt") -> None:
        """Save extracted text to a file."""
        try:
            with open(output_path, "w", encoding="utf-8") as file:
                file.write(text)
            print(f"✓ Text extracted and saved to {output_path}\n")
        except Exception as e:
            raise RuntimeError(f"Error saving extracted text: {str(e)}") from e
    
    def generate_summary(self, text: str) -> str:
        """
        Generate structured summary using OpenAI API.
        
        Args:
            text: The text to summarize
            
        Returns:
            Generated summary as a string
        """
        prompt = """Your job is to extract the following information from the text: 
Relative importance of: GPA, Course rigor, Test scores, Essay, Recommendation letters, 
Extracurriculars, Talent/ability, Interview, First-generation status, Demonstrated interest, 
Test policy (test-optional? test-blind?), Class rank importance, Early Decision vs. Regular 
Decision admit rates, Application requirements (portfolio, writing sample, etc.), Acceptance rate, 
Early Decision acceptance rate, Yield rate (how many admitted students choose to enroll), 
Geographic distribution, Gender breakdown, Ethnic demographics, Part-time vs. full-time student mix, 
% of students receiving financial aid, Average financial aid package, Need met % (e.g., "School meets 
100% of demonstrated need"), % of need met for typical student, % receiving merit aid, Average merit 
award, Total cost of attendance, Student-faculty ratio, Class size distribution (e.g., how many classes 
have <20 students), Most common majors, Degrees awarded by field. 

Extract this info and format it as a JSON object with clear keys for each category."""
        
        try:
            print("Generating summary...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts structured information from college admission documents and returns it as JSON."},
                    {"role": "user", "content": f"{prompt}\n\n{text}"}
                ],
                temperature=0.3,  # Lower temperature for more consistent, factual output
                response_format={"type": "json_object"}  # Request JSON format
            )
            
            summary = response.choices[0].message.content
            return summary
        except Exception as e:
            error_type = type(e).__name__
            if "RateLimitError" in error_type or "insufficient_quota" in str(e):
                raise RuntimeError(
                    "OpenAI API Quota Exceeded. Please check your plan and billing details at "
                    "https://platform.openai.com/account/billing"
                ) from e
            else:
                raise RuntimeError(f"Error generating summary: {error_type} - {str(e)}") from e
    
    def save_summary(self, summary: str, output_path: str = "output.txt", 
                     json_path: Optional[str] = None) -> None:
        """
        Save summary to file(s).
        
        Args:
            summary: The summary text to save
            output_path: Path for text output (default: output.txt)
            json_path: Optional path for JSON output (if summary is JSON)
        """
        try:
            # Save as text
            with open(output_path, "w", encoding="utf-8") as file:
                file.write(summary)
            
            # Try to parse and save as JSON if valid
            if json_path:
                try:
                    json_data = json.loads(summary)
                    with open(json_path, "w", encoding="utf-8") as file:
                        json.dump(json_data, file, indent=2, ensure_ascii=False)
                    print(f"✓ Summary saved as JSON to {json_path}")
                except json.JSONDecodeError:
                    print(f"⚠️  Summary is not valid JSON, skipping JSON save")
            
            print(f"✓ Summary saved to {output_path}")
        except Exception as e:
            raise RuntimeError(f"Error saving summary: {str(e)}") from e
    
    def parse(self, filename: str, save_text: bool = True, 
              save_json: bool = True) -> dict:
        """
        Main parsing function that orchestrates the entire process.
        
        Args:
            filename: Path to the PDF file
            save_text: Whether to save extracted text (default: True)
            save_json: Whether to save summary as JSON (default: True)
            
        Returns:
            Dictionary containing extracted text and summary
        """
        # Extract text
        text_output = self.extract_text_from_pdf(filename)
        
        # Save extracted text
        if save_text:
            base_name = Path(filename).stem
            text_output_path = f"{base_name}_extracted_text.txt"
            self.save_extracted_text(text_output, text_output_path)
        
        # Generate summary
        summary = self.generate_summary(text_output)
        
        # Save summary
        base_name = Path(filename).stem
        output_path = f"{base_name}_output.txt"
        json_path = f"{base_name}_output.json" if save_json else None
        self.save_summary(summary, output_path, json_path)
        
        # Print summary
        print("\n" + "="*60)
        print("SUMMARY:")
        print("="*60)
        print(summary)
        
        return {
            "extracted_text": text_output,
            "summary": summary,
            "text_file": text_output_path if save_text else None,
            "output_file": output_path,
            "json_file": json_path if save_json else None
        }


def main():
    """Main entry point for command-line usage."""
    try:
        # Get filename from user
        filename = input('Enter filename to parse: ').strip()
        
        if not filename:
            print("❌ Error: No filename provided")
            sys.exit(1)
        
        # Initialize parser (API key from environment variable)
        parser = PDFParser()
        
        # Parse the PDF
        result = parser.parse(filename)
        
        print("\n✓ Parsing completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

