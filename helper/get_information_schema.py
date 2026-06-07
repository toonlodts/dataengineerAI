import json

def get_information_schema(cursor, run_dir_name, phase):
    environment = None
    if phase == 'initial':
        environment = 'public'
    else:
        environment = phase + '_layer'

    # cursor.execute("""
    #                select table_name
    #                from information_schema.tables
    #                where table_schema = 'information_schema'
    #                UNION
    #                select table_name
    #                from information_schema.views
    #                where table_schema = 'information_schema'                   
    #                """)
    cursor.execute(f"select table_name from information_schema.tables where table_schema = '{environment}' and table_type = 'BASE TABLE';")
    objects_list = [row[0] for row in cursor.fetchall()]

    information_schema = {}

    for object_name in objects_list:
        try:
            # cursor.execute(f'select * from information_schema."{object_name}"')
    
            cursor.execute(f"SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema = '{environment}' AND table_name = '{object_name}' ORDER BY ordinal_position; " )
            
            columns = cursor.fetchall()

            information_schema[object_name] = {
                "columns": [
                    {
                        "name": col[0],
                        "type": col[1],
                        "nullable": col[2],
                    }
                    for col in columns
                ]
            }
            # print(information_schema)

            # cursor.execute(f"select k.table_name, k.column_name from information_schema.table_constraints t join information_schema.key_column_usage k on t.constraint_name = k.constraint_name where t.constraint_type = 'PRIMARY KEY' and t.table_schema = '{environment}'")

            # for object_name, column in cursor.fetchall():
            #     information_schema[object_name].setdefault("primary_keys", []).append(column)

        except Exception as e:
            print(f"error for {object_name}: {e}")

    with open(f"{run_dir_name}/information_schema_{phase}.json", "w") as file:
        json.dump(information_schema, file, default=str)