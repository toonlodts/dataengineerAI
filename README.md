The initial setup for this project:
- install PostgreSQL https://www.postgresql.org/download/
- install llama https://ollama.com/download/mac
- open PostgreSQL and create a database called 'chinook_template'
- create a schema called 'bronze_layer', 'silver_layer' and 'gold_layer'
- insert the data from /data/chinook_data.sql by running the SQL code directly on the database
- Create an example result for the desired question and place it in result.csv
- Alter prompts to fit your current requirement

To run, perform the following steps
1. Make sure PGAdmin is running so the postgres service is running
2. Open a terminal and do the 'ollama run llama3' command
3. run the command 'python run_experiment.py' for a single run or 'python experiment_loop.py' to run it 100 times
