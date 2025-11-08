from ultralytics import YOLO
import cv2

model = YOLO("yolov8n.pt") 

def detect(image, allowed_classes=['Rubik']):
    """
    Detect objects in an image and filter by allowed classes.
    
    Args:
        image: Path to image file or numpy array
        allowed_classes: List of class names to filter (default: ['Rubik'])
    
    Returns:
        dict: Contains 'detections' (list of filtered detections), 
              'annotated_image' (numpy array), and 'output_path' (str)
    """
    results = model.predict(image, save=True, conf=0.5) 

    # Optional: Accessing the results programmatically
    filtered_detections = []
    
    for result in results:
        # 'boxes' contains bounding box coordinates, class labels, and confidence scores
        boxes = result.boxes
        print(f"Detected {len(boxes)} objects.")
        
        # Get class names from the model
        class_names = model.names
        
        # Filter boxes by allowed classes
        for box in boxes:
            # box.xyxy: bounding box coordinates (x1, y1, x2, y2)
            # box.conf: confidence score
            # box.cls: class ID
            cls_id = int(box.cls.item())
            conf = box.conf.item()
            class_name = class_names[cls_id]
            coords = box.xyxy[0].cpu().numpy()
            
            # Only include detections that match allowed classes
            if class_name in allowed_classes:
                detection = {
                    'class': class_name,
                    'confidence': conf,
                    'bbox': coords.tolist(),
                    'class_id': cls_id
                }
                filtered_detections.append(detection)
                print(f"Class: {class_name}, Confidence: {conf:.2f}, Box: {coords}")
        
        print(f"Filtered to {len(filtered_detections)} objects matching allowed classes.")
        
        # Get the annotated image with bounding boxes and labels drawn
        annotated_image = result.plot()
        
        # Save the annotated image
        output_path = "detected_image.jpg"
        cv2.imwrite(output_path, annotated_image)
        print(f"Annotated image saved to {output_path}")
    
    return {
        'detections': filtered_detections,
        'annotated_image': annotated_image,
        'output_path': output_path
    }

if __name__ == "__main__":
    # Open webcam (0 is usually the default camera)
    cap = cv2.VideoCapture(0)
    
    # Check if webcam opened successfully
    if not cap.isOpened():
        print("Error: Could not open webcam")
        exit()
    
    print("Starting real-time detection. Press 'q' to quit.")
    
    # Define allowed classes for detection
    allowed_classes = ['Rubik']  # Modify this list as needed
    
    try:
        while True:
            # Read frame from webcam
            ret, frame = cap.read()
            
            if not ret:
                print("Error: Failed to grab frame")
                break
            
            # Run detection on the frame (save=False for better performance)
            results = model.predict(frame, save=False, conf=0.5, verbose=False)
            
            # Get annotated frame using YOLO's built-in plotting
            annotated_frame = frame.copy()
            
            for result in results:
                boxes = result.boxes
                class_names = model.names
                
                # Draw only allowed classes
                for box in boxes:
                    cls_id = int(box.cls.item())
                    conf = box.conf.item()
                    class_name = class_names[cls_id]
                    
                    # Only draw if class is in allowed_classes
                    if class_name in allowed_classes:
                        coords = box.xyxy[0].cpu().numpy()
                        x1, y1, x2, y2 = map(int, coords)
                        
                        # Draw bounding box (green color)
                        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        
                        # Draw label with confidence
                        label = f"{class_name}: {conf:.2f}"
                        (label_width, label_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                        label_y = max(y1, label_height + 10)
                        
                        # Draw label background rectangle
                        cv2.rectangle(annotated_frame, 
                                    (x1, label_y - label_height - 10), 
                                    (x1 + label_width, label_y + 5), 
                                    (0, 255, 0), -1)
                        
                        # Draw label text
                        cv2.putText(annotated_frame, label, 
                                  (x1, label_y), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
            
            # Display the annotated frame
            cv2.imshow('Real-time Detection', annotated_frame)
            
            # Break loop on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        # Release webcam and close windows
        cap.release()
        cv2.destroyAllWindows()
        print("Webcam released and windows closed")