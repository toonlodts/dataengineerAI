def evaluate_gold(cursor):
    r1 = test_fact_table_exists(cursor)
    r2 = test_dimension_table_exists(cursor)
    r3 = test_primary_keys(cursor)

    results = [r1, r2, r3]
    print(f"test results are: {results}")
    print(f"{sum(results)}/3 tests passed!")

    return r1, r2, r3

def get_all_tables(cursor):
    cursor.execute("""
                   SELECT table_name
                     FROM information_schema.tables
                    WHERE table_schema = 'gold_layer'
                          AND table_type = 'BASE TABLE'
                   """)
    return [row[0] for row in cursor.fetchall()]

def test_fact_table_exists(cursor):
    all_tables = get_all_tables(cursor)

    if [table for table in all_tables if table.startswith('fact_')] != []:
        return True
    return False

def test_dimension_table_exists(cursor):
    all_tables = get_all_tables(cursor)

    if [table for table in all_tables if table.startswith('dim_')] != []:
        return True
    return False 

def test_primary_keys(cursor):
    total_pk = 0
    table_count = 0
    for table in get_all_tables(cursor):
        table_count += 1
        cursor.execute(""" 
                        SELECT count(*)
                          FROM information_schema.table_constraints
                         WHERE table_name = %s
                               AND table_schema = 'gold_layer' 
                               AND constraint_type = 'PRIMARY KEY'
                       """, (table,))
        
        has_pk = cursor.fetchone()[0]

        if has_pk > 0:
            total_pk += 1 # we count it as 1 if the table has more than 1 PK, so we can say that we only need a 6, because that would imply all 6 tables have at least 1 PK
        
    return total_pk == table_count