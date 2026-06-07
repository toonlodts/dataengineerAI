table_dimensions = [
    (10, 412),
    (6, 2240),
    (10, 3503),
    (4, 347),
    (3, 275),
    (14, 59)
]


def evaluate_silver(cursor):
    r1 = test_table_count(cursor)
    r2 = test_column_count(cursor)
    r3 = test_row_count(cursor)
    r4 = test_no_duplicates(cursor)
    r5 = test_primary_keys(cursor)

    results = [r1, r2, r3, r4, r5]
    print(f"test results are: {results}")
    print(f"{sum(results)}/5 tests passed!")

    return r1, r2, r3, r4, r5

def test_table_count(cursor):
    cursor.execute("""
                    SELECT count(table_name)
                      FROM information_schema.tables
                     WHERE table_schema = 'silver_layer' 
                           AND table_type = 'BASE TABLE'
                   """)
    table_count = cursor.fetchone()[0]
    
    print("silver test 1: table count: ", table_count)
    return table_count == 6

def get_all_tables(cursor):
    cursor.execute("""
                   SELECT table_name
                     FROM information_schema.tables
                    WHERE table_schema = 'silver_layer'
                          AND table_type = 'BASE TABLE'
                   """)
    return [row[0] for row in cursor.fetchall()]

def get_silver_layer_table_dimensions(cursor):
    table_dimensions = {}
    table_list = get_all_tables(cursor)

    for table in table_list:
        cursor.execute(""" 
                        SELECT count(*)
                          FROM information_schema.columns
                         WHERE table_name = %s
                               AND table_schema = 'silver_layer'
                       """, (table,))
        column_count = cursor.fetchone()

        cursor.execute(f"SELECT count(*) FROM silver_layer.{table}")
        row_count = cursor.fetchone()

        table_dimensions[table] = [column_count, row_count]

    return table_dimensions

def test_column_count(cursor):
    expected_column_counts = sorted([s[0] for s in table_dimensions])
    actual_column_counts = sorted([s[0][0] for s in get_silver_layer_table_dimensions(cursor).values()])

    print("Silver test 2: expected: ", expected_column_counts, " and actual: ", actual_column_counts)

    return expected_column_counts == actual_column_counts
    
def test_row_count(cursor):
    expected_record_counts = sorted([s[1] for s in table_dimensions])
    actual_record_counts = sorted([s[1][0] for s in get_silver_layer_table_dimensions(cursor).values()])

    print("Silver test 3: expected: ", expected_record_counts, " and actual: ", actual_record_counts)
    return expected_record_counts == actual_record_counts

def test_no_duplicates(cursor):
    has_no_duplicates = True
    for table in get_all_tables(cursor): 
        cursor.execute(f"""
                        SELECT count(*)
                          FROM silver_layer.{table}
                        """)
        original_count = cursor.fetchone()[0]

        cursor.execute(f"""
                        SELECT count(*)
                          FROM (
                              SELECT DISTINCT * 
                                FROM silver_layer.{table})
                        """)
        
        distinct_count = cursor.fetchone()[0]

        if original_count > distinct_count:
            has_no_duplicates = False

    return has_no_duplicates

def test_primary_keys(cursor):
    total_pk = 0
    for table in get_all_tables(cursor):
        cursor.execute(""" 
                        SELECT count(*)
                          FROM information_schema.table_constraints
                         WHERE table_name = %s
                               AND table_schema = 'silver_layer' 
                               AND constraint_type = 'PRIMARY KEY'
                       """, (table,))
        
        has_pk = cursor.fetchone()[0]

        if has_pk > 0:
            total_pk += 1 # we count it as 1 if the table has more than 1 PK, so we can say that we only need a 6, because that would imply all 6 tables have at least 1 PK
        
    return total_pk == 6 