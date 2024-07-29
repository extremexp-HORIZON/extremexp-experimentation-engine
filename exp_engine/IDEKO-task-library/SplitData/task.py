import proactive_helper as ph
from sklearn.model_selection import train_test_split

features = ph.get_input("Features")

data = list()
data.append(df[indicator_list].to_numpy())

features = ph.get_input("Features")
labels = ph.get_input("Labels")

X_train, X_test, y_train, y_test = train_test_split(features, labels)

ph.save_output(("FeaturesTrain", X_train))
ph.save_output(("FeaturesTest", X_test))
ph.save_output(("LabelsTrain", y_train))
ph.save_output(("LabelsTest", y_test))
