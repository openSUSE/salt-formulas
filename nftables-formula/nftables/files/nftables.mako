## Write simple variables
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

## Write sets
## % for set, set_config in config.get('sets', {}).items():
## set ${set} = \
##   % if 'type' in set_config:
##   type ${set_config['type']}
##   % endif
##   % if 'flags' in set_config:
##   flags ${' '.join(set_config['flags'] if isinstance(set_config['flags'], list) else set_config['flags']}
##   % endif
##   % if set_config.get('auto-merge', False):
##   auto-merge
##   % endif
##   % if set_config.get('counter', False):
##   counter
##   % endif
##   % if 'policy' in set_config:
##   policy ${set_config['policy']}
##   % endif
##   % if 'timeout' in set_config:
##   timeout ${set_config['timeout']}
##   % endif
##   elements = { \
##     % for element in set_config['elements']:
##     ${element},
##     % endfor
##   }
## % endfor

## Write tables
% for table, table_config in config.get('tables', {}).items():
table ${table} ${table_config['type']} {
% for chain, chain_config in table_config.get('chains', {}).items():
  chain ${chain} {
    % if 'policy' in chain_config:
    policy ${chain_config['policy']}
    % endif
    % if 'jump' in chain_config:
    jump ${chain_config['jump']}
    % endif
    % for entry in chain_config.get('rules', []):
    ${entry}
    % endfor
  }
% endfor
}
% endfor
