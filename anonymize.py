import sys
import cv2
import os

class TextAnonymization:
    def __init__(self, detected_image_path, text_mask_path):
        self.detected_image_path = detected_image_path
        self.text_mask_path = text_mask_path
        self.detected_image = cv2.imread(self.detected_image_path)
        self.text_mask = cv2.imread(self.text_mask_path, cv2.IMREAD_GRAYSCALE)

    def inpaint_text(self):
        # Inpainting using the text mask
        inpainted_image = cv2.inpaint(self.detected_image, self.text_mask, inpaintRadius=1, flags=cv2.INPAINT_TELEA)
        return inpainted_image

if __name__ == "__main__":
    detected_image_path = sys.argv[1]  # Get the detected image path from command-line arguments
    text_mask_path = sys.argv[2]  # Get the text mask path from command-line arguments

    text_anonymization = TextAnonymization(detected_image_path, text_mask_path)
    anonymized_image = text_anonymization.inpaint_text()

    # Create the 'anonymized_images' directory if it doesn't exist
    anonymized_images_path = os.path.join(os.path.dirname(detected_image_path), 'temp_anonymized')
    if not os.path.exists(anonymized_images_path):
        os.makedirs(anonymized_images_path)
    elif not os.path.isdir(anonymized_images_path):
        print(f"The path {anonymized_images_path} already exists and is not a directory.")

    # Save the anonymized image in the 'anonymized_images' directory
    output_path = os.path.join(anonymized_images_path, f'anonymized_{os.path.basename(detected_image_path)}')
    cv2.imwrite(output_path, anonymized_image)
