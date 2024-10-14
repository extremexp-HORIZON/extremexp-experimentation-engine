workflow IDEKO_V1 {

  define task ReadData;
  define task AddPadding;
  define task SplitData;
  define task TrainModel;

  configure task ReadData {
    implementation "tasks/IDEKO/read_data.py";
    dependency "tasks/IDEKO/src/**";
  }

  configure task AddPadding {
      implementation "tasks/IDEKO/add_padding.py";
      dependency "tasks/IDEKO/src/**";
    }

  configure task SplitData {
      implementation "tasks/IDEKO/split_data.py";
      dependency "tasks/IDEKO/src/**";
  }

  configure task TrainModel {
      dependency "tasks/IDEKO/src/**";
  }

  START -> ReadData -> AddPadding -> SplitData -> TrainModel -> END;

  define data ReadDataInput;

  configure data ReadDataInput {
     path "datasets/ideko-subset/**";
  }

  ReadDataInput --> ReadData;

}

assembled workflow IDEKO_V1_NN from IDEKO_V1 {
  configure task TrainModel {
      implementation "tasks/IDEKO/train_nn.py";
  }
}

assembled workflow IDEKO_V1_RNN from IDEKO_V1 {
  configure task TrainModel {
      implementation "tasks/IDEKO/train_rnn.py";
  }
}


espace NNExpSpace of IDEKO_V1_RNN {

    configure self {
        method gridsearch as g;
        g.epochs_vp = enum(1,2);
        g.batch_size_vp = enum(64,80);
    }

    task TrainModel{
        param epochs = g.epochs_vp;
        param batchsize = g.batch_size_vp;
    }

}
