{% macro build_pr_database() %}

        {% if execute %}

            {# grab the pr name from the schema on target for the QA jobs #}
            {% set pr_name = target.schema.upper() %}

            {# Create a query to check to see if the PR database exists #}
            {% set database_info_query %}
                USE WAREHOUSE {{target.warehouse}};
                Select count(*) as num_count from SNOWFLAKE.INFORMATION_SCHEMA.DATABASES WHERE DATABASE_NAME = '{{pr_name}}'
            {% endset %}

            {# Grab the results #}
            {% set data_base_exists_check = run_query(database_info_query).columns[0].values()[0] %}

            {% if data_base_exists_check == 0 %}

                {% set create_database_query %}
                    USE WAREHOUSE {{target.warehouse}};
                    CREATE DATABASE IF NOT EXISTS {{pr_name}}
                {% endset %}

                {# run the database build #}
                {% do run_query(create_database_query) %}

            {% endif %}

        {% endif %}


{% endmacro %}