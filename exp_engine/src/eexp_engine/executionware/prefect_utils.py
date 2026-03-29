def _create_execution_engine_mapping(tasks, exp_engine_runtime_config):
    print("banaan")
    """Create mapping for execution engine"""
    mapping = {}
    # Mapping of output variable names to their generating tasks
    output_to_task = {}
    for t in tasks:
        for ds in t.output_files:
            # Map the output variable name to the task that generates it
            output_to_task[ds.name_in_task_signature] = t.name

    # Build the full mapping with source task information
    for t in tasks:
        # Initialize the task entry in the mapping
        if t.name not in mapping:
            mapping[t.name] = {"inputs": {}, "outputs": {}}

        ##### INPUTS #####
        for ds in t.input_files:
            # LOCAL FILE case
            if ds.path and (not ds.filename and not ds.project):
                mapping[t.name]["inputs"][ds.name_in_task_signature] = {
                    "file_name": ds.name,
                    "file_type": "local",
                    "file_path": ds.path,
                }
            # DDM case
            elif ds.filename and ds.project:
                uploaded_path = f"{ds.project}|{ds.filename if ds.filename else ''}"
                mapping[t.name]["inputs"][ds.name_in_task_signature] = {
                    "file_name": ds.name,
                    "file_type": "external",
                    "file_path": f"{ds.project}|{ds.filename if ds.filename else ''}",
                }
            # INTERMEDIATE FILE case
            else:
                # Find the task that generates this input by looking up the output variable name
                source_task = output_to_task.get(ds.name_in_generating_task)
                mapping[t.name]["inputs"][ds.name_in_task_signature] = {
                    "file_name": ds.name_in_generating_task,
                    "file_type": "intermediate",
                    "source_task": source_task,
                }

        ##### OUTPUTS #####
        for ds in t.output_files:
            # LOCAL FILE case
            if ds.path and (not ds.filename and not ds.project):
                mapping[t.name]["outputs"][ds.name_in_task_signature] = {
                    "file_name": ds.name,
                    "file_type": "local",
                    "file_path": ds.path,
                }
            # DDM case
            elif ds.filename and ds.project:
                mapping[t.name]["outputs"][ds.name_in_task_signature] = {
                    "file_name": ds.name,
                    "file_type": "external",
                    "file_path": f"{ds.project}|{ds.filename if ds.filename else ''}",
                }
            # INTERMEDIATE FILE case
            else:
                mapping[t.name]["outputs"][ds.name_in_task_signature] = {
                    "file_name": ds.name,
                    "file_type": "intermediate",
                }
    exp_engine_runtime_config["mapping"] = mapping
    print("EXECUTION ENGINE MAPPING")
    print("*****************")
    import pprint

    pprint.pp(mapping)
    print("*****************")
    return exp_engine_runtime_config

