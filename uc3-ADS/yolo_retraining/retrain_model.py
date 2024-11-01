import os
import torch
from pymongo import MongoClient
from pathlib import Path
from yolov5 import train  # YOLOv5 training script

# MongoDB Connection
client = MongoClient("mongodb://localhost:27017/")
db = client['yolo_database']
collection = db['training_data']

# Model and data directories
model_path = "/mnt/data/best.pt"
new_data_directory = Path("/mnt/data/new_training_data")
full_data_directory = Path("/mnt/data/full_training_data")

def fetch_new_data():
    """
    Fetch new data marked as 'new' in MongoDB, save it locally, 
    and update document status to 'processed' once saved.
    """
    if not new_data_directory.exists():
        os.makedirs(new_data_directory)

    new_data = []
    for document in collection.find({"status": "new"}):
        image_name = document['image_name']
        image_content = document['image_content']  # BLOB format in MongoDB

        # Save the image to disk
        image_path = new_data_directory / image_name
        with open(image_path, 'wb') as f:
            f.write(image_content)

        # Update MongoDB status to "processed"
        collection.update_one({"_id": document['_id']}, {"$set": {"status": "processed"}})
        new_data.append(image_name)

    return len(new_data) > 0

def prepare_data_for_training():
    """
    Move new images from new_data_directory to full_data_directory for training.
    """
    if not full_data_directory.exists():
        os.makedirs(full_data_directory)

    for file in os.listdir(new_data_directory):
        source = new_data_directory / file
        destination = full_data_directory / file
        if not destination.exists():
            os.rename(source, destination)

def retrain_yolov5_model():
    """
    Retrain YOLOv5 with both new and existing dataset.
    """
    data_yaml_path = "/mnt/data/fire_detection_dataset.yaml"

    train.run(
        data=data_yaml_path,
        weights=model_path,
        epochs=10,
        imgsz=640,
        name="fire_detection_improved"
    )
    print("YOLOv5 model retrained successfully.")

def monitor_new_data():
    """
    Monitor MongoDB in real-time for new data using Change Streams,
    and retrain YOLOv5 when new data is added.
    """
    print("Monitoring MongoDB for new data...")
    with collection.watch() as stream:
        for change in stream:
            if change['operationType'] == 'insert':
                print("New data detected, fetching files...")
                if fetch_new_data():
                    print("Preparing new data for training...")
                    prepare_data_for_training()
                    print("Retraining the YOLOv5 model...")
                    retrain_yolov5_model()
                else:
                    print("No new data to process.")

if __name__ == "__main__":
    monitor_new_data()