import cv2
import numpy as np
import os
from PIL import Image
import img2pdf
import PyPDF2
import io
import tkinter as tk
from tkinter import filedialog, ttk
import threading
import fitz  # PyMuPDF library for PDF flattening

def process_image(image):
    # Convert PIL Image to OpenCV format
    image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply adaptive thresholding
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 21, 10)

    # Create a horizontal kernel
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))

    # Detect horizontal lines
    detect_horizontal = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)

    # Dilate the lines to make them thicker
    dilate_kernel = np.ones((3, 3), np.uint8)
    dilated_lines = cv2.dilate(detect_horizontal, dilate_kernel, iterations=1)

    # Create a mask of the lines
    mask = cv2.bitwise_not(dilated_lines)

    # Apply the mask to the original image
    result = cv2.bitwise_and(image, image, mask=mask)

    # Inpaint the removed line areas
    inpainted = cv2.inpaint(result, dilated_lines, 5, cv2.INPAINT_TELEA)

    # Apply threshold with softening
    _, binary = cv2.threshold(cv2.cvtColor(inpainted, cv2.COLOR_BGR2GRAY), 200, 255, cv2.THRESH_BINARY)
    softened = cv2.GaussianBlur(binary, (5, 5), 0)
    final_result = cv2.bitwise_and(inpainted, inpainted)

    # Convert back to PIL Image
    return Image.fromarray(cv2.cvtColor(final_result, cv2.COLOR_BGR2RGB))

def process_pdf(pdf_path, progress_callback):
    processed_images = []
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_path)
        total_images = sum(1 for page in pdf_reader.pages for obj in page['/Resources']['/XObject'].get_object() if '/XObject' in page['/Resources'] and page['/Resources']['/XObject'].get_object()[obj]['/Subtype'] == '/Image')
        processed_count = 0
        
        progress_callback(0, total_images, "Extracting images")
        for page in pdf_reader.pages:
            if '/XObject' in page['/Resources']:
                xObject = page['/Resources']['/XObject'].get_object()
                for obj in xObject:
                    if xObject[obj]['/Subtype'] == '/Image':
                        size = (xObject[obj]['/Width'], xObject[obj]['/Height'])
                        data = xObject[obj].get_data()
                        img = Image.open(io.BytesIO(data))
                        processed_img = process_image(img)
                        processed_images.append(processed_img)
                        processed_count += 1
                        progress_callback(processed_count, total_images, "Extracting images")
    except Exception as e:
        print(f"Error extracting images: {str(e)}. Falling back to PDF flattening.")
        # Fallback to flattening PDF with high quality
        doc = fitz.open(pdf_path)
        total_images = len(doc)
        for i, page in enumerate(doc):
            pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))  # 300 DPI
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            processed_img = process_image(img)
            processed_images.append(processed_img)
            progress_callback(i + 1, total_images, "Flattening and processing PDF")
        doc.close()
    
    return processed_images

def process_file(input_path, output_path, progress_callback):
    if input_path.lower().endswith('.pdf'):
        # PDF mode
        progress_callback(0, 3, "Phase 1: Reading and processing PDF")
        processed_images = process_pdf(input_path, lambda current, total, phase: progress_callback(current, total, f"Phase 1: {phase}"))
        
        # Convert processed images to PDF
        a4_page_size = (img2pdf.mm_to_pt(210), img2pdf.mm_to_pt(297))  # A4 size in points
        layout_fun = img2pdf.get_layout_fun(a4_page_size)
        
        # Save processed images as temporary files
        temp_image_files = []
        progress_callback(0, 3, "Phase 2: Saving temporary images")
        for i, img in enumerate(processed_images):
            progress_callback(i + 1, len(processed_images), f"Phase 2: Saving temporary image {i+1}/{len(processed_images)}")
            temp_file = f"temp_image_{i}.png"
            img.save(temp_file, "PNG", dpi=(300, 300))  # Save at 300 DPI
            temp_image_files.append(temp_file)
        
        progress_callback(0, 3, "Phase 3: Creating final PDF")
        with open(output_path, "wb") as f:
            f.write(img2pdf.convert(temp_image_files, layout_fun=layout_fun, dpi=300))  # Set DPI to 300
        
        # Remove temporary files
        for temp_file in temp_image_files:
            os.remove(temp_file)
        
        progress_callback(3, 3, "Processing completed")
        print(f"Processed PDF saved as {output_path}")
    
    elif input_path.lower().endswith(('.png', '.jpg', '.jpeg')):
        # Image mode
        progress_callback(0, 2, "Phase 1: Processing image")
        img = Image.open(input_path)
        processed_img = process_image(img)
        progress_callback(1, 2, "Phase 2: Saving processed image")
        processed_img.save(output_path, dpi=(300, 300))  # Save at 300 DPI
        progress_callback(2, 2, "Processing completed")
        print(f"Processed image saved as {output_path}")
    
    else:
        print("Unsupported file format. Please use PDF or image files (PNG, JPG, JPEG).")

def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf"), ("Image files", "*.png;*.jpg;*.jpeg")])
    input_entry.delete(0, tk.END)
    input_entry.insert(0, file_path)

def select_output():
    file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf"), ("Image files", "*.png;*.jpg;*.jpeg")])
    output_entry.delete(0, tk.END)
    output_entry.insert(0, file_path)

def update_progress(current, total, phase):
    progress = int((current / total) * 100)
    progress_bar['value'] = progress
    status_label.config(text=f"{phase}")
    root.update_idletasks()

def start_processing():
    input_path = input_entry.get()
    output_path = output_entry.get()
    if input_path and output_path:
        process_button.config(state=tk.DISABLED)
        progress_bar['value'] = 0
        status_label.config(text="Processing...")
        
        def process_thread():
            process_file(input_path, output_path, update_progress)
            root.after(0, process_complete)
        
        threading.Thread(target=process_thread, daemon=True).start()
    else:
        status_label.config(text="Please select input and output files.")

def process_complete():
    process_button.config(state=tk.NORMAL)
    status_label.config(text="Processing completed!")

def main():
    global input_entry, output_entry, status_label, progress_bar, process_button, root
    
    root = tk.Tk()
    root.title("Image/PDF Processor")

    tk.Label(root, text="Input File:").grid(row=0, column=0, padx=5, pady=5)
    input_entry = tk.Entry(root, width=50)
    input_entry.grid(row=0, column=1, padx=5, pady=5)
    tk.Button(root, text="Browse", command=select_file).grid(row=0, column=2, padx=5, pady=5)

    tk.Label(root, text="Output File:").grid(row=1, column=0, padx=5, pady=5)
    output_entry = tk.Entry(root, width=50)
    output_entry.grid(row=1, column=1, padx=5, pady=5)
    tk.Button(root, text="Browse", command=select_output).grid(row=1, column=2, padx=5, pady=5)

    process_button = tk.Button(root, text="Start Processing", command=start_processing)
    process_button.grid(row=2, column=1, padx=5, pady=10)

    progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
    progress_bar.grid(row=3, column=1, padx=5, pady=5)

    status_label = tk.Label(root, text="")
    status_label.grid(row=4, column=1, padx=5, pady=5)

    root.mainloop()

if __name__ == "__main__":
    main()
