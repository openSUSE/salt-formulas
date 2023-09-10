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
    ## Establish correct rule order based on priority key
    <%
     combined_chain_config = {}
     combined_chain_config.update(chain_config.get('rules', {}))
     combined_chain_config.update(chain_config.get('meta', {}))
     for entry in sorted(combined_chain_config, key=lambda lowentry: combined_chain_config[lowentry].get('priority', 100)):
       combined_chain_config[entry] = combined_chain_config.pop(entry)
    %>
    % for entry, entry_config in combined_chain_config.items():
    ${entry}${entry_config.get(' action','')}
    % endfor
  }
% endfor
}
% endfor
