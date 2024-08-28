# 📄 Image/PDF Processor 🖼️

This application processes images and PDFs to remove horizontal lines and enhance the overall quality of the document.

## 🌟 Features

- Process single images (PNG, JPG, JPEG)
- Process multi-page PDF documents
- Remove horizontal lines from documents
- Enhance document quality
- User-friendly GUI interface

## 🖼️ Screenshots

![image](https://github.com/user-attachments/assets/861e6255-012e-44f1-b16e-b5ba534eb102)

Results: 
![image](https://github.com/user-attachments/assets/accb1f05-2202-409a-a432-a56271255492)



## 🛠️ Installation

1. Clone this repository or download the script.

2. Install the required dependencies:
bash
pip install opencv-python numpy Pillow img2pdf PyPDF2 PyMuPDF tkinter
## 🚀 Usage

1. Run the script:

2. Use the GUI to:
   - Select an input file (PDF or image)
   - Choose an output file location
   - Start the processing

3. Monitor the progress bar and status updates.

4. Once completed, find your processed file at the specified output location.

## 📋 Notes

- For PDFs, the script first attempts to extract and process individual images. If this fails, it falls back to flattening the entire PDF.
- The processed output maintains a high quality (300 DPI) for both images and PDFs.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

## 📜 License

[Add your license information here]
