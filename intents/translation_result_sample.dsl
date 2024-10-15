workflow IDEKO_WORKFLOW {

	define task DataLoading;
	define task Partitioning;
	define task Normalization;
	define task MissingValueRemoval;
	define task ModelTrain;
	define task ModelPredict;
	define task DataStoring;

	START -> DataLoading -> Partitioning -> Normalization -> MissingValueRemoval -> ModelTrain -> ModelPredict -> DataStoring -> END;

	configure task DataLoading {
		implementation "IDEKO-task-library.csv_local_reader";
	}

	configure task ModelPredict {
		implementation "IDEKO-task-library.nn_predictor";
	}

	configure task DataStoring {
		implementation "IDEKO-task-library.csv_local_writer";
	}

    // DATA
    define input data anomalies;
    anomalies --> DataLoading.ExternalDataFile;

    configure data anomalies {
        path "datasets/IDEKO/IDEKO1";
    }

}

workflow Workflow_0 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.decimal_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.convolutional_nn_learner";
	}

}

workflow Workflow_1 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.decimal_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.convolutional_nn_learner";
	}

}

workflow Workflow_2 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.min_max_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.convolutional_nn_learner";
	}

}

workflow Workflow_3 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.min_max_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.convolutional_nn_learner";
	}

}

workflow Workflow_4 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.z_score_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.convolutional_nn_learner";
	}

}

workflow Workflow_5 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.z_score_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.convolutional_nn_learner";
	}

}

workflow Workflow_6 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.decimal_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.convolutional_nn_learner";
	}

}

workflow Workflow_7 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.decimal_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.convolutional_nn_learner";
	}

}

workflow Workflow_8 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.min_max_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.convolutional_nn_learner";
	}

}

workflow Workflow_9 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.min_max_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.convolutional_nn_learner";
	}

}

workflow Workflow_10 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.z_score_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.convolutional_nn_learner";
	}

}

workflow Workflow_11 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.z_score_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.convolutional_nn_learner";
	}

}

workflow Workflow_12 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.decimal_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.convolutional_nn_learner";
	}

}

workflow Workflow_13 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.decimal_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.convolutional_nn_learner";
	}

}

workflow Workflow_14 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.min_max_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.convolutional_nn_learner";
	}

}

workflow Workflow_15 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.min_max_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.convolutional_nn_learner";
	}

}

workflow Workflow_16 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.z_score_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.convolutional_nn_learner";
	}

}

workflow Workflow_17 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.z_score_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.convolutional_nn_learner";
	}

}

workflow Workflow_18 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.decimal_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.convolutional_nn_learner";
	}

}

workflow Workflow_19 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.decimal_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.convolutional_nn_learner";
	}

}

workflow Workflow_20 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.min_max_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.convolutional_nn_learner";
	}

}

workflow Workflow_21 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.min_max_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.convolutional_nn_learner";
	}

}

workflow Workflow_22 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.z_score_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.convolutional_nn_learner";
	}

}

workflow Workflow_23 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.z_score_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.convolutional_nn_learner";
	}

}

workflow Workflow_24 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.decimal_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.feedforward_nn_learner";
	}

}

workflow Workflow_25 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.decimal_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.feedforward_nn_learner";
	}

}

workflow Workflow_26 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.min_max_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.feedforward_nn_learner";
	}

}

workflow Workflow_27 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.min_max_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.feedforward_nn_learner";
	}

}

workflow Workflow_28 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.z_score_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.feedforward_nn_learner";
	}

}

workflow Workflow_29 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.z_score_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.feedforward_nn_learner";
	}

}

workflow Workflow_30 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.decimal_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.feedforward_nn_learner";
	}

}

workflow Workflow_31 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.decimal_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.feedforward_nn_learner";
	}

}

workflow Workflow_32 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.min_max_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.feedforward_nn_learner";
	}

}

workflow Workflow_33 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.min_max_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.feedforward_nn_learner";
	}

}

workflow Workflow_34 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.z_score_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.feedforward_nn_learner";
	}

}

workflow Workflow_35 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.z_score_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.feedforward_nn_learner";
	}

}

workflow Workflow_36 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.decimal_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.feedforward_nn_learner";
	}

}

workflow Workflow_37 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.decimal_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.feedforward_nn_learner";
	}

}

workflow Workflow_38 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.min_max_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.feedforward_nn_learner";
	}

}

workflow Workflow_39 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.min_max_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.feedforward_nn_learner";
	}

}

workflow Workflow_40 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.z_score_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.feedforward_nn_learner";
	}

}

workflow Workflow_41 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.z_score_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.feedforward_nn_learner";
	}

}

workflow Workflow_42 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.decimal_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.feedforward_nn_learner";
	}

}

workflow Workflow_43 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.decimal_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.feedforward_nn_learner";
	}

}

workflow Workflow_44 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.min_max_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.feedforward_nn_learner";
	}

}

workflow Workflow_45 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.min_max_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.feedforward_nn_learner";
	}

}

workflow Workflow_46 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.z_score_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.feedforward_nn_learner";
	}

}

workflow Workflow_47 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.z_score_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.feedforward_nn_learner";
	}

}

workflow Workflow_48 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.decimal_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.lstm_nn_learner";
	}

}

workflow Workflow_49 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.decimal_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.lstm_nn_learner";
	}

}

workflow Workflow_50 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.min_max_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.lstm_nn_learner";
	}

}

workflow Workflow_51 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.min_max_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.lstm_nn_learner";
	}

}

workflow Workflow_52 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.z_score_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.lstm_nn_learner";
	}

}

workflow Workflow_53 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.z_score_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.lstm_nn_learner";
	}

}

workflow Workflow_54 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.decimal_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.lstm_nn_learner";
	}

}

workflow Workflow_55 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.decimal_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.lstm_nn_learner";
	}

}

workflow Workflow_56 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.min_max_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.lstm_nn_learner";
	}

}

workflow Workflow_57 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.min_max_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.lstm_nn_learner";
	}

}

workflow Workflow_58 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.z_score_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.lstm_nn_learner";
	}

}

workflow Workflow_59 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.z_score_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.lstm_nn_learner";
	}

}

workflow Workflow_60 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.decimal_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.lstm_nn_learner";
	}

}

workflow Workflow_61 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.decimal_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.lstm_nn_learner";
	}

}

workflow Workflow_62 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.min_max_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.lstm_nn_learner";
	}

}

workflow Workflow_63 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.min_max_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.lstm_nn_learner";
	}

}

workflow Workflow_64 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.z_score_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.lstm_nn_learner";
	}

}

workflow Workflow_65 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.z_score_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.lstm_nn_learner";
	}

}

workflow Workflow_66 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.decimal_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.lstm_nn_learner";
	}

}

workflow Workflow_67 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.decimal_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.lstm_nn_learner";
	}

}

workflow Workflow_68 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.min_max_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.lstm_nn_learner";
	}

}

workflow Workflow_69 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.min_max_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.lstm_nn_learner";
	}

}

workflow Workflow_70 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.z_score_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.lstm_nn_learner";
	}

}

workflow Workflow_71 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.z_score_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.lstm_nn_learner";
	}

}

workflow Workflow_72 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.decimal_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.recurrent_nn_learner";
	}

}

workflow Workflow_73 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.decimal_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.recurrent_nn_learner";
	}

}

workflow Workflow_74 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.min_max_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.recurrent_nn_learner";
	}

}

workflow Workflow_75 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.min_max_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.recurrent_nn_learner";
	}

}

workflow Workflow_76 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.z_score_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.recurrent_nn_learner";
	}

}

workflow Workflow_77 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.z_score_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.recurrent_nn_learner";
	}

}

workflow Workflow_78 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.decimal_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.recurrent_nn_learner";
	}

}

workflow Workflow_79 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.decimal_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.recurrent_nn_learner";
	}

}

workflow Workflow_80 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.min_max_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.recurrent_nn_learner";
	}

}

workflow Workflow_81 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.min_max_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.recurrent_nn_learner";
	}

}

workflow Workflow_82 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.z_score_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.recurrent_nn_learner";
	}

}

workflow Workflow_83 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.random_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.z_score_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.recurrent_nn_learner";
	}

}

workflow Workflow_84 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.decimal_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.recurrent_nn_learner";
	}

}

workflow Workflow_85 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.decimal_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.recurrent_nn_learner";
	}

}

workflow Workflow_86 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.min_max_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.recurrent_nn_learner";
	}

}

workflow Workflow_87 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.min_max_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.recurrent_nn_learner";
	}

}

workflow Workflow_88 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.z_score_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.recurrent_nn_learner";
	}

}

workflow Workflow_89 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_absolute_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.z_score_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.recurrent_nn_learner";
	}

}

workflow Workflow_90 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.decimal_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.recurrent_nn_learner";
	}

}

workflow Workflow_91 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.decimal_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.recurrent_nn_learner";
	}

}

workflow Workflow_92 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.min_max_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.recurrent_nn_learner";
	}

}

workflow Workflow_93 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.min_max_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.recurrent_nn_learner";
	}

}

workflow Workflow_94 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.z_score_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.drop_rows_with_missing_values";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.recurrent_nn_learner";
	}

}

workflow Workflow_95 from IDEKO_WORKFLOW{

	configure task Partitioning{
		implementation "IDEKO-task-library.top_k_relative_train_test_split";
	}

	configure task Normalization{
		implementation "IDEKO-task-library.z_score_scaling";
	}

	configure task MissingValueRemoval{
		implementation "IDEKO-task-library.mean_imputation";
	}

	configure task ModelTrain{
		implementation "IDEKO-task-library.recurrent_nn_learner";
	}

}

experiment IDEKO_EXPERIMENT {

	intent IDEKO;

	control {
		S_Workflow_0 -> S_Workflow_1;
		S_Workflow_1 -> S_Workflow_2;
		S_Workflow_2 -> S_Workflow_3;
		S_Workflow_3 -> S_Workflow_4;
		S_Workflow_4 -> S_Workflow_5;
		S_Workflow_5 -> S_Workflow_6;
		S_Workflow_6 -> S_Workflow_7;
		S_Workflow_7 -> S_Workflow_8;
		S_Workflow_8 -> S_Workflow_9;
		S_Workflow_9 -> S_Workflow_10;
		S_Workflow_10 -> S_Workflow_11;
		S_Workflow_11 -> S_Workflow_12;
		S_Workflow_12 -> S_Workflow_13;
		S_Workflow_13 -> S_Workflow_14;
		S_Workflow_14 -> S_Workflow_15;
		S_Workflow_15 -> S_Workflow_16;
		S_Workflow_16 -> S_Workflow_17;
		S_Workflow_17 -> S_Workflow_18;
		S_Workflow_18 -> S_Workflow_19;
		S_Workflow_19 -> S_Workflow_20;
		S_Workflow_20 -> S_Workflow_21;
		S_Workflow_21 -> S_Workflow_22;
		S_Workflow_22 -> S_Workflow_23;
		S_Workflow_23 -> S_Workflow_24;
		S_Workflow_24 -> S_Workflow_25;
		S_Workflow_25 -> S_Workflow_26;
		S_Workflow_26 -> S_Workflow_27;
		S_Workflow_27 -> S_Workflow_28;
		S_Workflow_28 -> S_Workflow_29;
		S_Workflow_29 -> S_Workflow_30;
		S_Workflow_30 -> S_Workflow_31;
		S_Workflow_31 -> S_Workflow_32;
		S_Workflow_32 -> S_Workflow_33;
		S_Workflow_33 -> S_Workflow_34;
		S_Workflow_34 -> S_Workflow_35;
		S_Workflow_35 -> S_Workflow_36;
		S_Workflow_36 -> S_Workflow_37;
		S_Workflow_37 -> S_Workflow_38;
		S_Workflow_38 -> S_Workflow_39;
		S_Workflow_39 -> S_Workflow_40;
		S_Workflow_40 -> S_Workflow_41;
		S_Workflow_41 -> S_Workflow_42;
		S_Workflow_42 -> S_Workflow_43;
		S_Workflow_43 -> S_Workflow_44;
		S_Workflow_44 -> S_Workflow_45;
		S_Workflow_45 -> S_Workflow_46;
		S_Workflow_46 -> S_Workflow_47;
		S_Workflow_47 -> S_Workflow_48;
		S_Workflow_48 -> S_Workflow_49;
		S_Workflow_49 -> S_Workflow_50;
		S_Workflow_50 -> S_Workflow_51;
		S_Workflow_51 -> S_Workflow_52;
		S_Workflow_52 -> S_Workflow_53;
		S_Workflow_53 -> S_Workflow_54;
		S_Workflow_54 -> S_Workflow_55;
		S_Workflow_55 -> S_Workflow_56;
		S_Workflow_56 -> S_Workflow_57;
		S_Workflow_57 -> S_Workflow_58;
		S_Workflow_58 -> S_Workflow_59;
		S_Workflow_59 -> S_Workflow_60;
		S_Workflow_60 -> S_Workflow_61;
		S_Workflow_61 -> S_Workflow_62;
		S_Workflow_62 -> S_Workflow_63;
		S_Workflow_63 -> S_Workflow_64;
		S_Workflow_64 -> S_Workflow_65;
		S_Workflow_65 -> S_Workflow_66;
		S_Workflow_66 -> S_Workflow_67;
		S_Workflow_67 -> S_Workflow_68;
		S_Workflow_68 -> S_Workflow_69;
		S_Workflow_69 -> S_Workflow_70;
		S_Workflow_70 -> S_Workflow_71;
		S_Workflow_71 -> S_Workflow_72;
		S_Workflow_72 -> S_Workflow_73;
		S_Workflow_73 -> S_Workflow_74;
		S_Workflow_74 -> S_Workflow_75;
		S_Workflow_75 -> S_Workflow_76;
		S_Workflow_76 -> S_Workflow_77;
		S_Workflow_77 -> S_Workflow_78;
		S_Workflow_78 -> S_Workflow_79;
		S_Workflow_79 -> S_Workflow_80;
		S_Workflow_80 -> S_Workflow_81;
		S_Workflow_81 -> S_Workflow_82;
		S_Workflow_82 -> S_Workflow_83;
		S_Workflow_83 -> S_Workflow_84;
		S_Workflow_84 -> S_Workflow_85;
		S_Workflow_85 -> S_Workflow_86;
		S_Workflow_86 -> S_Workflow_87;
		S_Workflow_87 -> S_Workflow_88;
		S_Workflow_88 -> S_Workflow_89;
		S_Workflow_89 -> S_Workflow_90;
		S_Workflow_90 -> S_Workflow_91;
		S_Workflow_91 -> S_Workflow_92;
		S_Workflow_92 -> S_Workflow_93;
		S_Workflow_93 -> S_Workflow_94;
		S_Workflow_94 -> S_Workflow_95;
	}

	space S_Workflow_0 of Workflow_0 { strategy gridsearch; }
	space S_Workflow_1 of Workflow_1 { strategy gridsearch; }
	space S_Workflow_2 of Workflow_2 { strategy gridsearch; }
	space S_Workflow_3 of Workflow_3 { strategy gridsearch; }
	space S_Workflow_4 of Workflow_4 { strategy gridsearch; }
	space S_Workflow_5 of Workflow_5 { strategy gridsearch; }
	space S_Workflow_6 of Workflow_6 { strategy gridsearch; }
	space S_Workflow_7 of Workflow_7 { strategy gridsearch; }
	space S_Workflow_8 of Workflow_8 { strategy gridsearch; }
	space S_Workflow_9 of Workflow_9 { strategy gridsearch; }
	space S_Workflow_10 of Workflow_10 { strategy gridsearch; }
	space S_Workflow_11 of Workflow_11 { strategy gridsearch; }
	space S_Workflow_12 of Workflow_12 { strategy gridsearch; }
	space S_Workflow_13 of Workflow_13 { strategy gridsearch; }
	space S_Workflow_14 of Workflow_14 { strategy gridsearch; }
	space S_Workflow_15 of Workflow_15 { strategy gridsearch; }
	space S_Workflow_16 of Workflow_16 { strategy gridsearch; }
	space S_Workflow_17 of Workflow_17 { strategy gridsearch; }
	space S_Workflow_18 of Workflow_18 { strategy gridsearch; }
	space S_Workflow_19 of Workflow_19 { strategy gridsearch; }
	space S_Workflow_20 of Workflow_20 { strategy gridsearch; }
	space S_Workflow_21 of Workflow_21 { strategy gridsearch; }
	space S_Workflow_22 of Workflow_22 { strategy gridsearch; }
	space S_Workflow_23 of Workflow_23 { strategy gridsearch; }
	space S_Workflow_24 of Workflow_24 { strategy gridsearch; }
	space S_Workflow_25 of Workflow_25 { strategy gridsearch; }
	space S_Workflow_26 of Workflow_26 { strategy gridsearch; }
	space S_Workflow_27 of Workflow_27 { strategy gridsearch; }
	space S_Workflow_28 of Workflow_28 { strategy gridsearch; }
	space S_Workflow_29 of Workflow_29 { strategy gridsearch; }
	space S_Workflow_30 of Workflow_30 { strategy gridsearch; }
	space S_Workflow_31 of Workflow_31 { strategy gridsearch; }
	space S_Workflow_32 of Workflow_32 { strategy gridsearch; }
	space S_Workflow_33 of Workflow_33 { strategy gridsearch; }
	space S_Workflow_34 of Workflow_34 { strategy gridsearch; }
	space S_Workflow_35 of Workflow_35 { strategy gridsearch; }
	space S_Workflow_36 of Workflow_36 { strategy gridsearch; }
	space S_Workflow_37 of Workflow_37 { strategy gridsearch; }
	space S_Workflow_38 of Workflow_38 { strategy gridsearch; }
	space S_Workflow_39 of Workflow_39 { strategy gridsearch; }
	space S_Workflow_40 of Workflow_40 { strategy gridsearch; }
	space S_Workflow_41 of Workflow_41 { strategy gridsearch; }
	space S_Workflow_42 of Workflow_42 { strategy gridsearch; }
	space S_Workflow_43 of Workflow_43 { strategy gridsearch; }
	space S_Workflow_44 of Workflow_44 { strategy gridsearch; }
	space S_Workflow_45 of Workflow_45 { strategy gridsearch; }
	space S_Workflow_46 of Workflow_46 { strategy gridsearch; }
	space S_Workflow_47 of Workflow_47 { strategy gridsearch; }
	space S_Workflow_48 of Workflow_48 { strategy gridsearch; }
	space S_Workflow_49 of Workflow_49 { strategy gridsearch; }
	space S_Workflow_50 of Workflow_50 { strategy gridsearch; }
	space S_Workflow_51 of Workflow_51 { strategy gridsearch; }
	space S_Workflow_52 of Workflow_52 { strategy gridsearch; }
	space S_Workflow_53 of Workflow_53 { strategy gridsearch; }
	space S_Workflow_54 of Workflow_54 { strategy gridsearch; }
	space S_Workflow_55 of Workflow_55 { strategy gridsearch; }
	space S_Workflow_56 of Workflow_56 { strategy gridsearch; }
	space S_Workflow_57 of Workflow_57 { strategy gridsearch; }
	space S_Workflow_58 of Workflow_58 { strategy gridsearch; }
	space S_Workflow_59 of Workflow_59 { strategy gridsearch; }
	space S_Workflow_60 of Workflow_60 { strategy gridsearch; }
	space S_Workflow_61 of Workflow_61 { strategy gridsearch; }
	space S_Workflow_62 of Workflow_62 { strategy gridsearch; }
	space S_Workflow_63 of Workflow_63 { strategy gridsearch; }
	space S_Workflow_64 of Workflow_64 { strategy gridsearch; }
	space S_Workflow_65 of Workflow_65 { strategy gridsearch; }
	space S_Workflow_66 of Workflow_66 { strategy gridsearch; }
	space S_Workflow_67 of Workflow_67 { strategy gridsearch; }
	space S_Workflow_68 of Workflow_68 { strategy gridsearch; }
	space S_Workflow_69 of Workflow_69 { strategy gridsearch; }
	space S_Workflow_70 of Workflow_70 { strategy gridsearch; }
	space S_Workflow_71 of Workflow_71 { strategy gridsearch; }
	space S_Workflow_72 of Workflow_72 { strategy gridsearch; }
	space S_Workflow_73 of Workflow_73 { strategy gridsearch; }
	space S_Workflow_74 of Workflow_74 { strategy gridsearch; }
	space S_Workflow_75 of Workflow_75 { strategy gridsearch; }
	space S_Workflow_76 of Workflow_76 { strategy gridsearch; }
	space S_Workflow_77 of Workflow_77 { strategy gridsearch; }
	space S_Workflow_78 of Workflow_78 { strategy gridsearch; }
	space S_Workflow_79 of Workflow_79 { strategy gridsearch; }
	space S_Workflow_80 of Workflow_80 { strategy gridsearch; }
	space S_Workflow_81 of Workflow_81 { strategy gridsearch; }
	space S_Workflow_82 of Workflow_82 { strategy gridsearch; }
	space S_Workflow_83 of Workflow_83 { strategy gridsearch; }
	space S_Workflow_84 of Workflow_84 { strategy gridsearch; }
	space S_Workflow_85 of Workflow_85 { strategy gridsearch; }
	space S_Workflow_86 of Workflow_86 { strategy gridsearch; }
	space S_Workflow_87 of Workflow_87 { strategy gridsearch; }
	space S_Workflow_88 of Workflow_88 { strategy gridsearch; }
	space S_Workflow_89 of Workflow_89 { strategy gridsearch; }
	space S_Workflow_90 of Workflow_90 { strategy gridsearch; }
	space S_Workflow_91 of Workflow_91 { strategy gridsearch; }
	space S_Workflow_92 of Workflow_92 { strategy gridsearch; }
	space S_Workflow_93 of Workflow_93 { strategy gridsearch; }
	space S_Workflow_94 of Workflow_94 { strategy gridsearch; }
	space S_Workflow_95 of Workflow_95 { strategy gridsearch; }

}
