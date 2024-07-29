workflow IDEKO {

  define task ReadData;
  define task AddPadding;
  define task SplitData;
  define task TrainModel;
  define task EvaluateModel;

  START -> ReadData -> AddPadding -> SplitData -> TrainModel -> EvaluateModel-> END;

  configure task ReadData {
    implementation "tasks/IDEKO/Binary_v1/read_data.py";
    dependency "tasks/IDEKO/Binary_v1/src/**";
  }

  configure task AddPadding {
      implementation "tasks/IDEKO/Binary_v1/add_padding.py";
      dependency "tasks/IDEKO/Binary_v1/src/**";
    }

  configure task SplitData {
      implementation "tasks/IDEKO/Binary_v1/split_data.py";
      dependency "tasks/IDEKO/Binary_v1/src/**";
  }

  configure task TrainModel {
      dependency "tasks/IDEKO/Binary_v1/src/**";
  }

  configure task EvaluateModel {
      implementation "tasks/IDEKO/Binary_v1/evaluate_model.py";
      dependency "tasks/IDEKO/Binary_v1/src/**";
  }

  define data InputData;

  configure data InputData {
    path "datasets/v1/ideko-subset/**";
    // path "datasets/ideko-full-dataset/**";
  }

  InputData --> ReadData;

}

workflow AW1 from IDEKO {
  configure task TrainModel {
      implementation "tasks/IDEKO/Binary_v1/train_nn.py";
  }
}

experiment EXP {

    intent FindBestClassifier;

    control {
        S1 -> E1;
    }

    space S1 of AW1 {
        strategy gridsearch;
        param epochs_vp = enum(2);
        param batch_size_vp = enum(64);

        configure task TrainModel {
             param epochs = epochs_vp;
             param batch_size = batch_size_vp;
        }
    }

    event E1 {
        type automated;
        condition "the accuracy of the 5 lastly trained ML models is > 50%";
        task check_accuracy_over_workflows_of_last_space;
    }

}



