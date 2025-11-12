from classes.ok import print_if_i_want
import kubeflow_helper as kh
import pandas as pd
import os

print("hello world")
MINIO_USERNAME = os.getenv("KUBEFLOW_MINIO_USERNAME")
MINIO_PASSWORD = os.getenv("KUBEFLOW_MINIO_PASSWORD")
print("Minio username:", MINIO_USERNAME)
print("Minio password:", MINIO_PASSWORD)

# Read S3 csv via pandas
file_obj = kh.load_dataset_local(variables, "task1inputfile")
df = pd.read_csv(file_obj)
print("Data from S3:", df.head())

kh.save_dataset_local(variables, resultMap, "output1", "I am here from task1")

print_if_i_want("Auto egine print apo to dependency file")
