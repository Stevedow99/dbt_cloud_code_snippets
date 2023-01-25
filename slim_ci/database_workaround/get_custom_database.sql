{% macro generate_database_name(custom_database_name=none, node=none) -%}

    {%- set default_database = target.database -%}

    {%- if target.name == 'qa' -%}

        {# grab the pr name from the schema on target for the QA jobs #}
        {% set pr_name = target.schema.upper() %}

        {{ pr_name }}

    {%- elif custom_database_name is none -%}

        {{ default_database }}

    {%- else -%}

        {{ custom_database_name | trim }}

    {%- endif -%}

{%- endmacro %}