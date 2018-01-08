# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from tank import Hook


class HieroGetExtraPublishData(Hook):
    """ Get a data dictionary for a PublishedFile to be updated in Shotgun. """
    def execute(self, task, **kwargs):
        """
        :param task: The Hiero Task that is currently being processed
        Return the dictionary to update the data for the PublishedFile in Shotgun
        or None if there is no extra information to publish.

        The track item associated with this task can be accessed via task._item.
        """

        #  CBSD Customization
        # ==============================
        sg_version_number = int(
            self.parent.execute_hook_method("hook_resolve_custom_strings", "getAutoVersion", task=task)
        )
        published_file_data = {
            'task': self.parent.context.task,
            'version_number': sg_version_number,
        }
        return published_file_data
        # ==============================
