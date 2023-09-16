## Write simple and set variables
% for variable, contents in config.get('variables', {}).items():
define ${variable} = \
  % if isinstance(contents, str):
${contents}
  % elif isinstance(contents, list):
{
% for value in contents:
  ${value},
% endfor
}
% endif
% endfor

## Write tables
% for table, table_config in config.get('tables', {}).items():
table ${table} ${table_config['type']} {
% for chain, chain_config in table_config.get('chains', {}).items():
  chain ${chain} {
    % if 'policy' in chain_config:
    policy ${chain_config['policy']}
    % endif
    % for entry in chain_config.get('rules', []):
    ${entry}
    % endfor
  }
% endfor
}
% endfor
