{% macro generate_schema_name(custom_schema_name, node) -%}

    {%- if target.name == 'qa' and custom_schema_name is not none -%}

        {{target.name}}_{{ custom_schema_name | trim }}

    {%- elif target.name == 'qa' and custom_schema_name is none -%}

        {{target.name}}

    {%- elif target.name != 'qa' and custom_schema_name is none -%}

        {{ default_schema }}

    {%- else -%}

        {{ default_schema }}_{{ custom_schema_name | trim }}

    {%- endif -%}


{%- endmacro %}