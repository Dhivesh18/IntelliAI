# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Add IAM Policy Binding."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.iap import util as iap_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
@base.DefaultUniverseOnly
class AddIamPolicyBinding(base.Command):
  """Add IAM policy binding to an IAP TCP Tunnel Destination Group resource.

  Adds a policy binding to the IAM policy of an IAP TCP Tunnel Destination Group
  resource. One binding consists of a member, a role, and an optional condition.
  """
  detailed_help = {
      'EXAMPLES':
          """\
          To add an IAM policy binding for the role of
          'roles/iap.tunnelResourceAccessor' for the user 'test-user@gmail.com'
          in the group 'my-group' located in the region 'us-west1', run:

            $ {command} --member='user:test-user@gmail.com'
               --role='roles/iap.tunnelResourceAccessor'
               --dest-group='my-group' --region='us-west1'

          To add an IAM policy binding for the role of
          'roles/iap.tunnelResourceAccessor' for all authenticated users in the
          group 'my-group' located in the region 'us-west1', run:

            $ {command} --member='allAuthenticatedUsers'
              --role='roles/iap.tunnelResourceAccessor'
              --dest-group='my-group' --region='us-west1'

          To add an IAM policy binding which expires at the end of the year 2018
          for the role of 'roles/iap.tunnelResourceAccessor' and the user
          'test-user@gmail.com' in the group 'my-group' located in the region
          'us-west1', run:

            $ {command} --member='user:test-user@gmail.com'
                --role='roles/iap.tunnelResourceAccessor'
                --condition='expression=request.time <
                timestamp("2019-01-01T00:00:00Z"),title=expires_end_of_2018,
                description=Expires at midnight on 2018-12-31'
                --dest-group='my-group' --region='us-west1'

          See https://cloud.google.com/iam/docs/managing-policies for details of
          policy role and member types.
  """,
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    iap_util.AddAddIamPolicyBindingArgs(parser)
    iap_util.AddIamDestGroupArgs(parser)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The specified function with its description and configured filter.
    """
    condition = iam_util.ValidateAndExtractConditionMutexRole(args)
    iap_iam_ref = iap_util.ParseIapDestGroupResource(self.ReleaseTrack(), args)
    return iap_iam_ref.AddIamPolicyBinding(args.member, args.role, condition)
