from classes.ok import print_if_i_want
import kubeflow_helper as kh
import pandas as pd
import os
from io import BytesIO

print("hello world")
MINIO_USERNAME = os.getenv("KUBEFLOW_MINIO_USERNAME")
MINIO_PASSWORD = os.getenv("KUBEFLOW_MINIO_PASSWORD")
print("Minio username:", MINIO_USERNAME)
print("Minio password:", MINIO_PASSWORD)

# Read S3 csv via pandas
[file_obj] = kh.load_datasets_ddm(variables, "task1inputfile", resultMap)
df = pd.read_csv(file_obj)
print("Data from S3:", df.head())

kh.save_datasets_ddm(variables, resultMap, "output2", [df.to_csv(index=False).encode('utf-8')])

kh.save_datasets_ddm(variables, resultMap, "output1", ["I am here from task1".encode('utf-8')])

resultMap["I2CAT_accuracy"] = float(0.92)

print_if_i_want("Auto egine print apo to dependency file")
