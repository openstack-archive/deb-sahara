# Copyright (c) 2014 Red Hat Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# job execution status
JOB_STATUS_DONEWITHERROR = 'DONEWITHERROR'
JOB_STATUS_FAILED = 'FAILED'
JOB_STATUS_KILLED = 'KILLED'
JOB_STATUS_PENDING = 'PENDING'
JOB_STATUS_RUNNING = 'RUNNING'
JOB_STATUS_SUCCEEDED = 'SUCCEEDED'
JOB_STATUS_TOBEKILLED = 'TOBEKILLED'
# statuses for terminated jobs
JOB_STATUSES_TERMINATED = [
    JOB_STATUS_DONEWITHERROR,
    JOB_STATUS_FAILED,
    JOB_STATUS_KILLED,
    JOB_STATUS_SUCCEEDED
]
# job type separator character
JOB_TYPE_SEP = '.'
# job sub types available
JOB_SUBTYPE_STREAMING = 'Streaming'
JOB_SUBTYPE_NONE = ''
# job types available
JOB_TYPE_HIVE = 'Hive'
JOB_TYPE_JAVA = 'Java'
JOB_TYPE_MAPREDUCE = 'MapReduce'
JOB_TYPE_SPARK = 'Spark'
JOB_TYPE_MAPREDUCE_STREAMING = (JOB_TYPE_MAPREDUCE + JOB_TYPE_SEP +
                                JOB_SUBTYPE_STREAMING)
JOB_TYPE_PIG = 'Pig'
# job type groupings available
JOB_TYPES_ALL = [
    JOB_TYPE_HIVE,
    JOB_TYPE_JAVA,
    JOB_TYPE_MAPREDUCE,
    JOB_TYPE_MAPREDUCE_STREAMING,
    JOB_TYPE_PIG,
    JOB_TYPE_SPARK
]


def split_job_type(job_type):
    '''Split a job type string into a type and subtype

    The split is done on the first '.'.  A subtype will
    always be returned, even if it is empty.
    '''
    type_info = job_type.split(JOB_TYPE_SEP, 1)
    if len(type_info) == 1:
        type_info.append('')
    return type_info


def compare_job_type(job_type, *args, **kwargs):
    '''Compare a job type against a list of job types

    :param job_type: The job type being compared
    :param *args: A list of types to compare against
    :param strict: Passed as a keyword arg. Default is False.
                   If strict is False, job_type will be compared
                   with and without its subtype indicator.
    :returns: True if job_type is present in the list, False otherwise
    '''
    strict = kwargs.get('strict', False)
    res = job_type in args
    if res or strict or JOB_TYPE_SEP not in job_type:
        return res

    jtype, jsubtype = split_job_type(job_type)
    return jtype in args


def get_hive_shared_conf_path(hdfs_user):
    return "/user/%s/conf/hive-site.xml" % hdfs_user
