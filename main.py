import os
from flask import Flask, render_template, jsonify, url_for, redirect, request, send_from_directory
from PIL import Image
import pytesseract
from werkzeug.utils import secure_filename

class main:
    def __init__(self, name: str):
        self.app = Flask(name)
        self.app.config["DEBUG"] = True
        
        # Configuration for the ocr folder
        self.UPLOAD_FOLDER = 'ocr'
        self.ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
        self.app.config["UPLOAD_FOLDER"] = self.UPLOAD_FOLDER
        
        # Register routes AFTER UPLOAD_FOLDER is configured
        self._register_routes()
    
    #check if the file uploaded is correct
    def allowed_file(self, filename) -> bool:
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS
    
    #method for route
    def _register_routes(self) -> None:
        self.app.add_url_rule('/', view_func=self.home_page, methods=["GET", "POST"])
        self.app.add_url_rule('/crop/<filename>', view_func=self.crop_page, methods=["GET", "POST"])
        self.app.add_url_rule('/ocr/<filename>', view_func=self.uploaded_file)
        self.app.add_url_rule('/scamcheck', view_func=self.scam_check, methods=["GET","POST"])
    
    def home_page(self) -> render_template:
        #POST image upload
        if request.method == "POST":
            #check if the file exists
            if 'file' not in request.files:
                return redirect(request.url)
            file = request.files['file']
            #check that there is a file that doesnt have an empty name
            if file.filename == '':
                return redirect(request.url)
            #check that if there is a file it also is an allowed file type
            if file and self.allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(self.app.config['UPLOAD_FOLDER'], filename))
                name, ext = os.path.splitext(filename)
                new_filename = f"{name}1{ext}"
                file.seek(0)
                file.save(os.path.join(self.app.config['UPLOAD_FOLDER'], new_filename))
    
                # Fetch text inputs typed before uploading
                phone = request.form.get("phone", "")
                message = request.form.get("message", "")
                return redirect(url_for('crop_page', filename=filename)) 
        return render_template('index.html')
    
    def crop_page(self, filename):
        file_path = os.path.join(self.app.config['UPLOAD_FOLDER'], filename)
        name, ext = os.path.splitext(filename)
        new_filename = f"{name}1{ext}"
        newfile_path =os.path.join(self.app.config['UPLOAD_FOLDER'], new_filename)
        #this is where the cropping happens
        if request.method == 'POST':
            x1 = float(request.form.get('x1', 0))
            y1 = float(request.form.get('y1', 0))
            width1 = float(request.form.get('width1', 0))
            height1 = float(request.form.get('height1', 0))
            x2 = float(request.form.get('x2', 0))
            y2 = float(request.form.get('y2', 0))
            width2 = float(request.form.get('width2', 0))
            height2 = float(request.form.get('height2', 0))
            if width1 > 0 and height1 > 0:
                with Image.open(file_path) as img:
                    phonebox = (x1, y1, x1 + width1, y1 + height1)
                    cropped_img = img.crop(phonebox)
                    cropped_img.save(file_path)
            if width2 > 0 and height2 > 0:
                with Image.open(newfile_path) as img:
                    messagebox = (x2, y2, x2 + width2, y2 + height2)
                    cropped_img = img.crop(messagebox)
                    cropped_img.save(newfile_path)     
            #argument position order mapping to definition
            phonenumber = self.read_image_text(image_path=file_path)
            print(phonenumber)
            messagecontent = self.read_image_text(image_path=newfile_path)      
            # Redirect back home, passing the dictionary results out into the URL strings
            return redirect(url_for('scam_check',phonenumber =phonenumber, messagecontent= messagecontent))           
        return render_template('crop.html', filename=filename,filename2 = new_filename)
    
    def uploaded_file(self, filename):
        return send_from_directory(self.app.config['UPLOAD_FOLDER'], filename)
     
    def read_image_text(self,image_path):
        phone_number_and_message = {}
        try:
            img = Image.open(image_path)
            extracted_text = pytesseract.image_to_string(img).strip()
            os.remove(image_path)
            print(extracted_text)
            return extracted_text
            
            # If phone field was empty, populate phone. Otherwise populate message.
        except Exception as e:
            # Return current status even if OCR throws an exception error
            phone_number_and_message["message"] = f"OCR Error: {e}"
            os.remove(image_path)
            return phone_number_and_message            

    def scam_check(self):
        phonenumber = request.args.get("phonenumber") # or whatever your form fields are named
        messagecontent = request.args.get("messagecontent")
        print(phonenumber)
        print(messagecontent)
        
        return render_template('scam.html', phone=phonenumber, message=messagecontent)
 
    def run(self, host: str = "0.0.0.0", port: int = 5000) -> None:
        self.app.run(host=host, port=port)
        
if __name__ == "__main__":
    server = main(__name__)
    server.run()
