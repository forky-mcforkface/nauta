#
# INTEL CONFIDENTIAL
# Copyright (c) 2018 Intel Corporation
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material contains trade secrets and proprietary
# and confidential information of Intel or its suppliers and licensors. The
# Material is protected by worldwide copyright and trade secret laws and treaty
# provisions. No part of the Material may be used, copied, reproduced, modified,
# published, uploaded, posted, transmitted, distributed, or disclosed in any way
# without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
#

from collections import namedtuple
import dateutil
from enum import Enum
from typing import List

from platform_resources.platform_resource_model import PlatformResource
from platform_resources.run_model import Run, RunStatus
from util.system import format_timestamp_for_cli


class UserStatus(Enum):
    DEFINED = 'DEFINED'
    CREATED = 'CREATED'
    UNKNOWN = 'UNKNOWN'


class User(PlatformResource):

    UserCliModel = namedtuple('UserCliModel', ['name', 'created', 'date_of_last_submitted_job',
                                               'running_jobs', 'queued_jobs'])

    def __init__(self, name: str, uid: int, state: UserStatus = UserStatus.DEFINED,
                 creation_timestamp: str = None, experiment_runs: List[Run] = None):
        self.name = name
        self.uid = uid
        self.state = state
        self.creation_timestamp = creation_timestamp
        self.experiment_runs = experiment_runs if experiment_runs else []


    @classmethod
    def from_k8s_response_dict(cls, object_dict: dict):
        name = "---"
        uid = "---"
        state = UserStatus.UNKNOWN
        creation_timestamp = "---"

        if object_dict:
            if object_dict.get('metadata'):
                    name = object_dict.get('metadata').get('name')
                    creation_timestamp = object_dict.get('metadata').get('creationTimestamp')

            if object_dict.get('spec'):
                uid = object_dict.get('spec').get('uid')

                if object_dict.get('spec').get('state'):
                    state = UserStatus[object_dict.get('spec').get('state')]

        return cls(name=name,
                   uid=uid,
                   state=state,
                   creation_timestamp=creation_timestamp)


    @property
    def cli_representation(self):
        return User.UserCliModel(name=self.name, created=format_timestamp_for_cli(self.creation_timestamp),
                                 running_jobs=self.running_jobs_count, queued_jobs=self.queued_jobs_count,
                                 date_of_last_submitted_job=format_timestamp_for_cli(self.date_of_last_submitted_job)
                                                            if self.date_of_last_submitted_job is not None else None)

    @property
    def date_of_last_submitted_job(self) -> str or None:
        if self.experiment_runs:
            return sorted((run for run in self.experiment_runs),
                          key=lambda run: dateutil.parser.parse(run.creation_timestamp))[-1].creation_timestamp
        else:
            return None

    @property
    def running_jobs_count(self) -> int:
        return len([run for run in self.experiment_runs if run.state == RunStatus.RUNNING])

    @property
    def queued_jobs_count(self) -> int:
        return len([run for run in self.experiment_runs if run.state == RunStatus.QUEUED])
