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
        self.thresholds = [200, 140, 80, 90, 100, 70]  # Threshold values

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

        # Convert image to grayscale
        gray_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)

        # Apply thresholding using each threshold value and combine masks
        for threshold in self.thresholds:
            _, binary_image = cv2.threshold(gray_image, threshold, 255, cv2.THRESH_BINARY)
            mask = self.detect_connected_components(binary_image, mask)

        return mask

    # Function to calculate distance between two points
    def distance(self, p1, p2):
        return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5

    # Function to detect connected components and update the mask
    def detect_connected_components(self, binary_image, mask, min_size=1, max_size=20, min_distance=20):
        # Connected Component Analysis
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary_image, connectivity=8)

        # List to store the bounding boxes of connected components
        bounding_boxes = []

        # Iterate through connected components
        for label in range(1, num_labels):
            # Filter components based on size
            if min_size <= stats[label, cv2.CC_STAT_AREA] <= max_size:
                x, y, w, h = stats[label, cv2.CC_STAT_LEFT], stats[label, cv2.CC_STAT_TOP], stats[label, cv2.CC_STAT_WIDTH], stats[label, cv2.CC_STAT_HEIGHT]
                bounding_boxes.append((x, y, w, h))

        # List to store indices of components that should be detected
        detected_indices = []

        # Iterate through bounding boxes
        for i, (x1, y1, w1, h1) in enumerate(bounding_boxes):
            # Flag to indicate if a nearby component is found
            nearby_found = False

            # Calculate centroid of the current component
            centroid1 = (x1 + w1 // 2, y1 + h1 // 2)

            # Check against other bounding boxes
            for j, (x2, y2, w2, h2) in enumerate(bounding_boxes):
                if i != j:  # Skip self-comparison
                    # Calculate centroid of the other component
                    centroid2 = (x2 + w2 // 2, y2 + h2 // 2)
                    # Calculate distance between centroids
                    if self.distance(centroid1, centroid2) < min_distance:  # Check against distance threshold
                        nearby_found = True
                        break

            if nearby_found:
                detected_indices.append(i)

        # Draw detected objects on the mask
        for index in detected_indices:
            x, y, w, h = bounding_boxes[index]
            cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)

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

# Function to calculate distance between two points
def distance(p1, p2):
    return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5

# Function to detect connected components and update the mask
def detect_connected_components(binary_image, mask, min_size=1, max_size=20, min_distance=20):
    # Connected Component Analysis
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary_image, connectivity=8)

    # List to store the bounding boxes of connected components
    bounding_boxes = []

    # Iterate through connected components
    for label in range(1, num_labels):
        # Filter components based on size
        if min_size <= stats[label, cv2.CC_STAT_AREA] <= max_size:
            x, y, w, h = stats[label, cv2.CC_STAT_LEFT], stats[label, cv2.CC_STAT_TOP], stats[label, cv2.CC_STAT_WIDTH], stats[label, cv2.CC_STAT_HEIGHT]
            bounding_boxes.append((x, y, w, h))

    # List to store indices of components that should be detected
    detected_indices = []

    # Iterate through bounding boxes
    for i, (x1, y1, w1, h1) in enumerate(bounding_boxes):
        # Flag to indicate if a nearby component is found
        nearby_found = False

        # Calculate centroid of the current component
        centroid1 = (x1 + w1 // 2, y1 + h1 // 2)

        # Check against other bounding boxes
        for j, (x2, y2, w2, h2) in enumerate(bounding_boxes):
            if i != j:  # Skip self-comparison
                # Calculate centroid of the other component
                centroid2 = (x2 + w2 // 2, y2 + h2 // 2)
                # Calculate distance between centroids
                if distance(centroid1, centroid2) < min_distance:  # Check against distance threshold
                    nearby_found = True
                    break

        if nearby_found:
            detected_indices.append(i)

    # Draw detected objects on the mask
    for index in detected_indices:
        x, y, w, h = bounding_boxes[index]
        cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)

    return mask

if __name__ == "__main__":
    image_path = sys.argv[1]  # Get the image path from command-line arguments
    run_detection(image_path)
