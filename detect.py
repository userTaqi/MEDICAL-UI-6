import cv2
import numpy as np
import keras_ocr
from ultralytics import YOLO
import sys
import os

class TextAndObjectMasking:
    def __init__(self, image_path):
        self.image_path = image_path
        self.image = cv2.imread(self.image_path)
        self.text_pipeline = keras_ocr.pipeline.Pipeline()
        self.object_model = YOLO("calModel.pt")  # Load the YOLO model with specified weights

    def detect_text_and_objects(self):
        # Detect text regions
        detected_text = self.text_pipeline.recognize([self.image_path])
        text_regions = [bbox for _, bbox in detected_text[0]]

        # Make predictions on the current input image for object detection
        object_results = self.object_model.predict(source=self.image_path, show=False, show_labels=False, save=False)

        return text_regions, detected_text[0], object_results

    def create_text_and_object_mask(self, text_regions, object_results):
        mask = np.zeros_like(self.image)

        # Add text regions to the mask
        for bbox in text_regions:
            pts = np.array(bbox, dtype=np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.fillPoly(mask, [pts], (255, 255, 255))

        # Add object detection results to the mask
        for r in object_results:
            for bbox in r.boxes.xyxy:
                x_min, y_min, x_max, y_max = map(int, bbox)
                cv2.rectangle(mask, (x_min, y_min), (x_max, y_max), (255), -1)

        return mask

if __name__ == "__main__":
    image_path = sys.argv[1]  # Get the image path from command-line arguments
    masking = TextAndObjectMasking(image_path)
    text_regions, detected_text, object_results = masking.detect_text_and_objects()

    # Create the 'detected_images' directory if it doesn't exist
    detected_images_path = os.path.join(os.path.dirname(image_path), 'temp_detected')
    if not os.path.exists(detected_images_path):
        os.makedirs(detected_images_path)

    # Save the image with bounding boxes for both text and object detection
    image_with_boxes = masking.image.copy()

    # Draw bounding boxes for text detection
    for _, bbox in detected_text:
        pts = np.array(bbox, dtype=np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.polylines(image_with_boxes, [pts], isClosed=True, color=(0, 255, 0), thickness=1)

    # Draw bounding boxes for object detection
    for r in object_results:
        for bbox in r.boxes.xyxy:
            x_min, y_min, x_max, y_max = map(int, bbox)
            cv2.rectangle(image_with_boxes, (x_min, y_min), (x_max, y_max), (255, 0, 0), 2)

    boxes_output_path = os.path.join(detected_images_path, f'boxes_{os.path.basename(image_path)}')
    cv2.imwrite(boxes_output_path, image_with_boxes)

    # Save the image with combined masks
    combined_mask = masking.create_text_and_object_mask(text_regions, object_results)
    mask_output_path = os.path.join(detected_images_path, f'mask_{os.path.basename(image_path)}')
    cv2.imwrite(mask_output_path, combined_mask)
