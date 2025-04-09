{#-
Salt state file for cleaning PHP FPM
Copyright (C) 2025 Georg Pfuetzenreuter <mail+opensuse@georg-pfuetzenreuter.net>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
-#}

php-fpm_package:
  pkg.removed:
    - pkgs:
        - php7-fpm
        - php8-fpm
        - php9-fpm

php-fpm_config:
  file.absent:
    - names:
        - /etc/php7/fpm
        - /etc/php8/fpm
        - /etc/php9/fpm
