import cv2
import numpy as np
import os
from PIL import Image
import img2pdf
import PyPDF2
import io

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

def process_pdf(pdf_path):
    processed_images = []
    pdf_reader = PyPDF2.PdfReader(pdf_path)
    
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
    
    return processed_images

def main():
    filename = input("Enter the filename in the current folder: ")
    
    if filename.lower().endswith('.pdf'):
        # PDF mode
        processed_images = process_pdf(filename)
        
        # Convert processed images to PDF
        a4_page_size = (img2pdf.mm_to_pt(210), img2pdf.mm_to_pt(297))  # A4 size in points
        layout_fun = img2pdf.get_layout_fun(a4_page_size)
        
        # Save processed images as temporary files
        temp_image_files = []
        for i, img in enumerate(processed_images):
            temp_file = f"temp_image_{i}.png"
            img.save(temp_file, "PNG")
            temp_image_files.append(temp_file)
        
        output_filename = f"processed_{filename}"
        with open(output_filename, "wb") as f:
            f.write(img2pdf.convert(temp_image_files, layout_fun=layout_fun))
        
        # Remove temporary files
        for temp_file in temp_image_files:
            os.remove(temp_file)
        
        print(f"Processed PDF saved as {output_filename}")
    
    elif filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        # Image mode
        img = Image.open(filename)
        processed_img = process_image(img)
        
        output_filename = f"processed_{filename}"
        processed_img.save(output_filename)
        
        print(f"Processed image saved as {output_filename}")
    
    else:
        print("Unsupported file format. Please use PDF or image files (PNG, JPG, JPEG).")

if __name__ == "__main__":
    main()
