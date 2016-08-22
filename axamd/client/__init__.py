# Copyright (c) 2016 by Farsight Security, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__import__('pkg_resources').declare_namespace(__name__)

__all__ = ['client', 'Client',
        'anomaly', 'Anomaly',
        'exceptions', 'AXAMDException', 'ValidationError', 'ProblemDetails',
        '__title__', '__description__', '__version__',
        '__author__', '__author_email__',
        '__uri__', '__license__', '__copyright__', '__classifiers__',
        ]

from .__about__ import (__title__, __version__, __description__,
        __author__, __author_email__,
        __uri__, __license__, __copyright__, __classifiers__,
        )
from .client import Anomaly, Client, __doc__
from .exceptions import AXAMDException, ValidationError, ProblemDetails

__doc__ # make pyflakes happy
