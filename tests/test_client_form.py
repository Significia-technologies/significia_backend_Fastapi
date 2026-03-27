import os
import sys

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.reports.client_blank_form import generate_client_blank_form

def test_generate_form():
    print("Generating Client Blank Form...")
    try:
        buffer = generate_client_blank_form()
        with open("client_form_test.pdf", "wb") as f:
            f.write(buffer.getvalue())
        print("Success! PDF saved as client_form_test.pdf")
    except Exception as e:
        print(f"Failed to generate form: {e}")

if __name__ == "__main__":
    test_generate_form()
