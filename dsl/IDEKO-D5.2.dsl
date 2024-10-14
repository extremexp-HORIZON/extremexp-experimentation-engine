workflow IDEKO_V1 {

  define task ReadData;
  define task AddPadding;
  define task SayHello;
  define task SplitData;
  define task TrainModel;
  //define task EvaluateModel;

  define operator op1;

  // START -> ReadData -> AddPadding -> SplitData -> TrainModel  -> END;
  START -> ReadData;
  ReadData -> "AAA" ? AddPadding : SayHello -> SplitData;

  //AddPadding -> SplitData;
  //SayHello -> SplitData;

  SplitData -> TrainModel  -> END;


  configure task ReadData {
    implementation "tasks/IDEKO/read_data.py";
    dependency "tasks/IDEKO/src/**";
  }

  configure task AddPadding {
      implementation "tasks/IDEKO/add_padding.py";
      dependency "tasks/IDEKO/src/**";
    }

  configure task SayHello {
      implementation "tasks/IDEKO/say_hello.py";
      dependency "tasks/IDEKO/src/**";
    }

  configure task SplitData {
      implementation "tasks/IDEKO/split_data.py";
      dependency "tasks/IDEKO/src/**";
  }

  configure task TrainModel {
      dependency "tasks/IDEKO/src/**";
  }

  //configure task EvaluateModel {
      //implementation "tasks/IDEKO/evaluate_model.py";
      //dependency "tasks/IDEKO/src/**";
  //}



  // DATA
  define data InputData;
  define data RawData;
  define data PaddedData;
  define data TrainingData;
  define data TestData;

  // DATA CONNECTIONS

  //InputData --> ReadData --> RawData --> AddPadding --> PaddedData --> SplitData;
  //SplitData --> TrainingData;
  //SplitData --> TestData;
  //TrainingData --> TrainModel;
  //TestData --> TrainModel;



  configure data InputData {
     path "datasets/ideko-subset/**";
  }

  InputData --> ReadData;

}

// comparison on performance of models
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
        // the onces below are training parameter, but also structural parameters could be used
        g.epochs_vp = enum(1);
        g.batch_size_vp = enum(64, 128);
    }

    task TrainModel{
         param epochs = g.epochs_vp;
         param batch_size = g.batch_size_vp;
    }

}

