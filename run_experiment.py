import argparse
import os
import pandas as pd
import ast
from connection.postgres_con import PostgresConnection
from connection.llama_con import LlamaConnection
from evaluations.eval_bronze_layer import evaluate_bronze
from evaluations.eval_silver_layer import evaluate_silver
from evaluations.eval_gold_layer import evaluate_gold


from helper.run_id_helper import get_run_id
from helper.get_information_schema import get_information_schema

def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("database")
    arg_parser.add_argument("model")
    arg_parser.add_argument("experiment_type")
    arg_parser.add_argument("run_count")

    args = arg_parser.parse_args()

    selected_database = args.database
    selected_model = args.model
    run_count = args.run_count
    print("runner script received run count: ", run_count)
    experiment_type = args.experiment_type

    current_run_id = get_run_id()
    new_database_name = selected_database+'_'+current_run_id
    print(f"Currently working on run: {current_run_id}, with database_name: {new_database_name}")

    run_dir_name = f"runs/{selected_database}/{current_run_id}"
    os.makedirs(run_dir_name)
    os.makedirs(run_dir_name+'/bronze')
    os.makedirs(run_dir_name+'/silver')
    os.makedirs(run_dir_name+'/gold')
    os.makedirs(run_dir_name+'/bi')
    print(f"Creating a new folder for this run: {run_dir_name}")
    


    print("Running experiments for database: ", selected_database)
    print("While using the model: ", selected_model)

    # code to duplicate the database
    database = PostgresConnection()
    database.connect()
    db_conn = database.get_connection()
    cursor = db_conn.cursor()
    cursor.execute("CREATE DATABASE "+new_database_name+" WITH TEMPLATE "+selected_database+"_template;")
    cursor.close()
    db_conn.close()

    database = PostgresConnection(database=new_database_name)
    database.connect()
    db_conn = database.get_connection()
    cursor = db_conn.cursor()


    llama = LlamaConnection()
    
    run_counter = 0
    prev_counter = 0
    information_schema_list = ['initial', 'bronze', 'silver', 'gold']
    llm_schema_list = ['bronze', 'silver', 'gold', 'bi']
    layer_counter = []
    
    for i in range(0, 4):
        get_information_schema(cursor, run_dir_name, information_schema_list[i])
        prepare_prompt(llm_schema_list[i], run_dir_name, selected_database)
        with open(f"{run_dir_name}/{llm_schema_list[i]}/prompt.txt", 'r') as prompt: 
            prompt_details = prompt.read()
            working_output = False
            while working_output == False:
                run_counter += 1
                if run_counter - prev_counter > 100:
                    raise Exception("Too much runs required, not going to get a result!")
                print(f"Running {llm_schema_list[i]} for run number: ", run_counter)
                query = llama.perform_llama_api_call(prompt_details, run_dir_name, llm_schema_list[i])
                working_output = validate_llama_output(cursor, query)

        with open(f"{run_dir_name}/{llm_schema_list[i]}/llama_output.txt", 'r') as query:
            query_details = query.read()
            try: 
                cursor.execute(query_details)
                if i == 3: # this indicates that we are running the BI layer query, we should save this one in a file
                    final_result = cursor.fetchall()

                    columns = [c[0] for c in cursor.description]

                    result_df = pd.DataFrame(final_result, columns=columns)

                    result_df.to_csv(f"{run_dir_name}/{llm_schema_list[i]}/result.csv", index=False)

            except Exception as e:
                pass
                #print("Error in bronze: ", e)
        print(f"{llm_schema_list[i].upper()} WORKING AT COUNT: ", run_counter)
        print(f"{llm_schema_list[i]} took {run_counter - prev_counter} run(s) to be succesfull")
        db_conn.commit()
        layer_counter.append([llm_schema_list[i], run_counter - prev_counter])
        prev_counter = run_counter

    # Run experiments!
    b1, b2, b3, b4, b5 = evaluate_bronze(cursor)
    s1, s2, s3, s4, s5 = evaluate_silver(cursor)
    g1, g2, g3 = evaluate_gold(cursor)



    # Compare final results!
    df_generated = pd.read_csv(f"{run_dir_name}/bi/result.csv")
    df_manual = pd.read_csv("templates/chinook/result.csv")

    results_equal = df_generated.sort_index(axis=1).sort_values(by=list(df_generated.columns)).reset_index(drop=True).equals(df_manual.sort_index(axis=1).sort_values(by=list(df_manual.columns)).reset_index(drop=True))


    print("results of the runcounters: ", layer_counter)
    print("Results of the result: ", results_equal)
    cursor.close()
    db_conn.close()

    # code to drop the database
    database = PostgresConnection()
    database.connect()
    db_conn = database.get_connection()
    cursor = db_conn.cursor()
    cursor.execute("DROP DATABASE "+new_database_name+";")
    cursor.close()
    db_conn.close()

    results_dataframe = pd.DataFrame({
        "experiment_type": experiment_type,
        "run_id": current_run_id,
        "bronze_runs": layer_counter[0][1],
        "bronze_1": b1,
        "bronze_2": b2,
        "bronze_3": b3,
        "bronze_4": b4,
        "bronze 5": b5,
        "silver_runs": layer_counter[1][1],
        "silver_1": s1,
        "silver_2": s2,
        "silver_3": s3,
        "silver_4": s4,
        "silver_5": s5,
        "gold_runs": layer_counter[2][1],
        "gold_1": g1,
        "gold_2": g2,
        "gold_3": g3,
        "bi_runs": layer_counter[3][1],
        "bi_1": results_equal,
    }, index=[0])

    if int(run_count) == 1:
        results_dataframe.to_csv("experiment_result.csv", index=False)
    else:
        prev_result = pd.read_csv("experiment_result.csv")
        df_combined = pd.concat([prev_result, results_dataframe], ignore_index = True)
        df_combined.to_csv("experiment_result.csv", index=False)
    
    return 0


def prepare_prompt(layer, run_dir_name, selected_database):
    original_layer = layer
    prompt_template = f"templates/{selected_database}/{layer}_prompt.txt"

    if layer == 'bronze':
        information_schema = run_dir_name+"/information_schema_initial.json"
    elif layer == 'silver':
        information_schema = run_dir_name+"/information_schema_bronze.json"
    elif layer == 'gold': 
        information_schema = run_dir_name+"/information_schema_silver.json"
    elif layer == 'bi': 
        information_schema = run_dir_name+"/information_schema_gold.json"


    output_file = f"{run_dir_name}/{original_layer}/prompt.txt"
    with open(prompt_template, 'r') as f1, open(information_schema, 'r') as f2, open(output_file, 'w') as out:
        out.write(f1.read())
        out.write(f2.read())

def validate_llama_output(cursor, query ):
    try:
        cursor.execute("BEGIN")
        cursor.execute(query)
        cursor.execute("ROLLBACK")
        return True
    except Exception as e:
        #print("Sql wrong: ", e)
        cursor.execute("ROLLBACK")
        return False
              

    

if __name__ == "__main__":
    main()