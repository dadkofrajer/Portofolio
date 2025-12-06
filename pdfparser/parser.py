import pdfplumber
from openai import OpenAI
import os



def parser():


    filename = input('Enter filename to parse: ')

    if(".pdf" not in filename):
        return

    with pdfplumber.open(filename) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"

    return text

    


text_output = parser()

# Save raw extracted text to a separate file
with open("extracted_text.txt", "w", encoding="utf-8") as file:
    file.write(text_output)
print("✓ Text extracted and saved to extracted_text.txt\n")

# Get API key from environment variable
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set. Please set it before running this script.")

client = OpenAI(api_key=api_key)

try:
    print("Generating summary...")
    response = client.chat.completions.create(
        model="gpt-4o-mini",  
        messages=[
            {"role": "user", "content": f"Your job is to extract the following information from the text: Relative importance of: GPA, Course rigor, Test scores, Essay, Recommendation letters, Extracurriculars, Talent/ability, Interview, First-generation status, Demonstrated interest, Test policy (test-optional? test-blind?), Class rank importance, Early Decision vs. Regular Decision admit rates, Application requirements (portfolio, writing sample, etc.), Acceptance rate, Early Decision acceptance rate, Yield rate (how many admitted students choose to enroll), Geographic distribution, Gender breakdown, Ethnic demographics, Part-time vs. full-time student mix, of students receiving financial aid, Average financial aid package, Need met % (e.g., “School meets 100% of demonstrated need”), % of need met for typical student, % receiving merit aid, Average merit award, Total cost of attendance, Student-faculty ratio, Class size distribution (e.g., how many classes have <20 students), Most common majors, Degrees awarded by field. Extract this info and save it in a json file with the same name as the input file.\n\n{text_output}"}


        ]
    )
    
    summary = response.choices[0].message.content
    
    # Save summary to output.txt
    with open("output.txt", "w", encoding="utf-8") as file:
        file.write(summary)
    
    print("\n" + "="*60)
    print("SUMMARY:")
    print("="*60)
    print(summary)
    print("\n✓ Summary saved to output.txt")
    
except Exception as e:
    error_type = type(e).__name__
    if "RateLimitError" in error_type or "insufficient_quota" in str(e):
        print("\n❌ Error: OpenAI API Quota Exceeded")
        print("You have exceeded your current quota. Please check your plan and billing details.")
        print("Visit: https://platform.openai.com/account/billing")
        print("\nThe extracted text has been saved to extracted_text.txt, but summarization failed due to quota limits.")
    else:
        print(f"\n❌ Error occurred: {error_type}")
        print(f"Details: {str(e)}")
    exit(1)