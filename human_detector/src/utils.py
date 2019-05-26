# Copyright 2019 Cyril Poulet, cyril.poulet@centraliens.net
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import json
import decimal
from tensorflow.python.client import device_lib


def get_available_gpus():
    """
    Lists all available GPUs 

    :returns: list of gpu names
    """
    local_device_protos = device_lib.list_local_devices()
    return [x.name for x in local_device_protos if x.device_type == 'GPU']


def camelcase_to_underscores(str_val):
    """
    Turns strings in camel case to underscores  (eg ThisExampleRocks -> this_example_rocks)

    :return: string
    """
    str_val = str_val[0].lower() + str_val[1:]
    for i in range(1, len(str_val)-2):
        if str_val[i].isupper():
            str_val = str_val[:i] + '_' + str_val[i].lower() + str_val[i+1:]
    str_val = str_val[:-1] + str_val[-1].lower()
    return str_val


# Helper class to convert a DynamoDB item to JSON.
class DecimalDecoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if abs(o) % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalDecoder, self).default(o)
