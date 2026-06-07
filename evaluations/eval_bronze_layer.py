from psycopg2 import sql

table_dimensions = [
    (10, 412),
    (6, 2240),
    (10, 3503),
    (4, 347),
    (3, 275),
    (14, 59)
]

def evaluate_bronze(cursor):
    r1 = test_table_count(cursor)
    r2 = test_column_count(cursor)
    r3 = test_row_count(cursor)
    r4 = test_ingestion_time_column_present(cursor)
    r5 = test_ingestion_time_column_filled(cursor)

    results = [r1, r2, r3, r4, r5]
    print(f"test results are: {results}")
    print(f"{sum(results)}/5 tests passed!")
    return r1, r2, r3, r4, r5

def test_table_count(cursor):
    cursor.execute("""
                    SELECT count(table_name)
                      FROM information_schema.tables
                     WHERE table_schema = 'bronze_layer' 
                           AND table_type = 'BASE TABLE'
                   """)
    table_count = cursor.fetchone()[0]
    print("Bronze test 1: table count: ", table_count)
    return table_count == 6

def get_all_tables(cursor):
    cursor.execute("""
                   SELECT table_name
                     FROM information_schema.tables
                    WHERE table_schema = 'bronze_layer'
                          AND table_type = 'BASE TABLE'
                   """)
    return [row[0] for row in cursor.fetchall()]

def get_bronze_layer_table_dimensions(cursor):
    table_dimensions = {}
    table_list = get_all_tables(cursor)

    for table in table_list:
        cursor.execute(""" 
                        SELECT count(*)
                          FROM information_schema.columns
                         WHERE table_name = %s
                               AND table_schema = 'bronze_layer'
                       """, (table,))
        column_count = cursor.fetchone()

        cursor.execute(f"SELECT count(*) FROM bronze_layer.{table}")
        row_count = cursor.fetchone()

        table_dimensions[table] = (column_count, row_count)

    return table_dimensions

def test_column_count(cursor):
    expected_column_counts = sorted([s[0] for s in table_dimensions])
    actual_column_counts = sorted([s[0][0] for s in get_bronze_layer_table_dimensions(cursor).values()])
    
    print("Bronze test 2: expected: ", expected_column_counts, " and actual: ", actual_column_counts)
    return expected_column_counts == actual_column_counts
    
def test_row_count(cursor):
    expected_record_counts = sorted([s[1] for s in table_dimensions])
    actual_record_counts = sorted([s[1][0] for s in get_bronze_layer_table_dimensions(cursor).values()])

    print("Bronze test 3: expected: ", expected_record_counts, " and actual: ", actual_record_counts)
    return expected_record_counts == actual_record_counts

def test_ingestion_time_column_present(cursor):
    cursor.execute(""" 
                    SELECT count(*)
                      FROM information_schema.columns
                     WHERE table_schema = 'bronze_layer'
                           AND column_name = 'ingestion_time'
                   """)   
    column_count = cursor.fetchone()[0]
    print("COLUMN count for ingestion time: ", column_count)
    return column_count == 6 # this column should occur 6 times because we have 6 tables

def test_ingestion_time_column_filled(cursor):
    table_list = get_all_tables(cursor)
    total_null_count = 0

    for table in table_list:
        query = sql.SQL("""
                        SELECT COUNT(*)
                          FROM bronze_layer.{}
                         WHERE ingestion_time IS NULL
                       """).format(sql.Identifier(table))
        cursor.execute(query)
        total_null_count += cursor.fetchone()[0]
    
    return total_null_count == 0
