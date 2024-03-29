import cv2
import numpy as np
import keras_ocr
from ultralytics import YOLO
import os
import sys

class TextAndObjectMasking:
    def __init__(self, image_path):
        self.image_path = image_path
        self.image = cv2.imread(self.image_path)
        self.text_pipeline = keras_ocr.pipeline.Pipeline()
        self.object_model = YOLO("calModelv2.pt")  # Load the YOLO model with specified weights

    def detect_text_regions(self):
        # Detect text regions
        detected_text = self.text_pipeline.recognize([self.image_path])
        text_regions = [bbox for _, bbox in detected_text[0]]
        return text_regions

    def detect_objects(self):
        # Make predictions on the current input image for object detection
        object_results = self.object_model.predict(source=self.image_path, show=False, show_labels=False, save=False)
        return object_results

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

def run_detection(image_path):
    masking = TextAndObjectMasking(image_path)
    text_regions = masking.detect_text_regions()
    object_results = masking.detect_objects()

    # Create the 'temp_detected' and 'temp_masked' directories if they don't exist
    temp_detected_path = os.path.join(os.path.dirname(image_path), 'temp_detected')
    if not os.path.exists(temp_detected_path):
        os.makedirs(temp_detected_path)
    temp_masked_path = os.path.join(os.path.dirname(image_path), 'temp_masked')
    if not os.path.exists(temp_masked_path):
        os.makedirs(temp_masked_path)
    temp_coordinates_path = os.path.join(os.path.dirname(image_path), 'temp_coordinates')
    if not os.path.exists(temp_coordinates_path):
        os.makedirs(temp_coordinates_path)

    # Save the image with bounding boxes for both text and object detection
    image_with_boxes = masking.image.copy()

    # Draw bounding boxes for text detection and save coordinates to a text file
    detected_text = masking.text_pipeline.recognize([image_path])[0]
    text_coords_file = open(os.path.join(temp_coordinates_path, f'text_coordinates_{os.path.basename(image_path)}.txt'), 'w')
    for i, bbox in enumerate(detected_text):
        pts = np.array(bbox[1], dtype=np.int32).reshape((-1, 1, 2))
        cv2.polylines(image_with_boxes, [pts], isClosed=True, color=(0, 255, 0), thickness=1)
        text_coords_file.write(f"Text {i+1} coordinates: {bbox[1]}\n")
    text_coords_file.close()

    # Draw bounding boxes for object detection and save coordinates to a text file
    object_coords_file = open(os.path.join(temp_coordinates_path, f'object_coordinates_{os.path.basename(image_path)}.txt'), 'w')
    for r_idx, r in enumerate(object_results):
        for b_idx, bbox in enumerate(r.boxes.xyxy):
            x_min, y_min, x_max, y_max = map(int, bbox)
            cv2.rectangle(image_with_boxes, (x_min, y_min), (x_max, y_max), (255, 0, 0), 2)
            object_coords_file.write(f"Object {r_idx+1}, Box {b_idx+1} coordinates: {bbox}\n")
    object_coords_file.close()

    boxes_output_path = os.path.join(temp_detected_path, f'boxes_{os.path.basename(image_path)}')
    cv2.imwrite(boxes_output_path, image_with_boxes)

    # Save the image with combined masks
    combined_mask = masking.create_text_and_object_mask(text_regions, object_results)
    mask_output_path = os.path.join(temp_masked_path, f'mask_{os.path.basename(image_path)}')
    cv2.imwrite(mask_output_path, combined_mask)



if __name__ == "__main__":
    image_path = sys.argv[1]  # Get the image path from command-line arguments
    run_detection(image_path)
