import os
import base64
import requests
from flask import Flask, render_template, request, flash, session
from werkzeug.utils import secure_filename
import openai

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def generate_prompt_from_image(image_data, api_key):
    try:
        openai.api_key = api_key

        messages = [{
            "role": "user",
            "content": [{
                "type": "text",
                "text": "Generate a creative writing prompt based on this image. The prompt should be imaginative and open-ended, encouraging storytelling or poetry."
            }, {
                "type": "image_url",
                "image_url": image_data
            }]
        }]

        response = openai.Completion.create(
            engine="text-davinci-003",
            max_tokens=300,
            n=1,
            stop=None,
            temperature=0.5,
            prompt=messages
        )

        return response.choices[0].text.strip()

    except openai.error.OpenAIError as e:
        return f"An error occurred while calling the OpenAI API: {str(e)}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if 'previous_prompts' not in session:
        session['previous_prompts'] = []

    if request.method == 'POST':
        api_key = request.form['api_key']
        if not api_key:
            flash('Please provide an OpenAI API key')
            return render_template('upload.html', previous_prompts=session['previous_prompts'])

        image_url = request.form['image_url']
        if image_url:
            try:
                response = requests.get(image_url)
                if response.status_code == 200:
                    image_data = f"data:image/jpeg;base64,{base64.b64encode(response.content).decode()}"
                    prompt = generate_prompt_from_image(image_data, api_key)
                else:
                    flash('Failed to fetch image from URL')
                    return render_template('upload.html', previous_prompts=session['previous_prompts'])
            except Exception as e:
                flash(f'Error processing image URL: {str(e)}')
                return render_template('upload.html', previous_prompts=session['previous_prompts'])

        elif 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                flash('No selected file')
                return render_template('upload.html', previous_prompts=session['previous_prompts'])
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # Ensure upload folder exists
                file.save(filepath)
                image_data = f"data:image/jpeg;base64,{encode_image(filepath)}"
                prompt = generate_prompt_from_image(image_data, api_key)
                os.remove(filepath)  # Remove the file after processing
            else:
                flash('Invalid file type')
                return render_template('upload.html', previous_prompts=session['previous_prompts'])
        else:
            flash('No file uploaded or URL provided')
            return render_template('upload.html', previous_prompts=session['previous_prompts'])

        # Save the new prompt and keep only the last 5
        session['previous_prompts'].insert(0, prompt)
        session['previous_prompts'] = session['previous_prompts'][:5]
        session.modified = True

        return render_template('upload.html', prompt=prompt, previous_prompts=session['previous_prompts'])

    return render_template('upload.html', previous_prompts=session['previous_prompts'])

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, host="0.0.0.0", port=8085)