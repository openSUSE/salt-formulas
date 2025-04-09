# Salt states for the PHP FPM

(the PHP FastCGI Process Manager)

## Available states

- `php-fpm.manage`

  Installs and configures [PHP FPM](https://www.php.net/manual/en/install.fpm.php).

  Conflicts with `php-fpm.clean`.

- `php-fpm.clean`

  Purges PHP FPM.

  Conflicts with `php-fpm.manage`.

- `php-fpm`

  Calls `php-fpm.manage` if a `php-fpm` pillar is defined, and `php-fpm.clean` otherwise.

  This is the recommended state to include.
