import google.generativeai as genai
import sys
import os

# Assuming your API key is in a file named env.py
try:
    import env
except ImportError:
    print("Error: env.py not found. Please create this file with your API key.")
    sys.exit(1)

# Configure the API key from the imported env file
genai.configure(api_key=env.GEMINI_API_KEY)
model_name = env.MODEL_NAME

def send_prompt_from_file(file_path):
    """
    Reads a prompt from a file, sends it to the Gemini API, and prints the response.
    """
    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"Error: The file '{file_path}' was not found.")
        return

    try:
        # Read the content of the file
        with open(file_path, 'r', encoding='utf-8') as file:
            prompt = file.read()

        # Initialize the Gemini model
        model = genai.GenerativeModel(model_name)

        print(f"Sending prompt from '{file_path}' to Gemini...")

        # Send the prompt to the model and get the response
        response = model.generate_content(prompt)

        # Print the generated content
        print("\n--- Gemini's Response ---")
        print(response.text)
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Check if a filename argument was provided
    if len(sys.argv) < 2:
        print("Usage: python api_test.py <filename>")
        sys.exit(1)

    # Get the filename from the command-line arguments
    input_file = sys.argv[1]
    
    # Run the main function with the provided filename
    send_prompt_from_file(input_file)
