# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

#  CBSD Customization
# ===========================
import os
from pprint import pprint
# ===========================

from tank import Hook


class HieroUpdateVersionData(Hook):
    """ Update the data dictionary for a Version to be created in Shotgun. """
    def execute(self, version_data, task, **kwargs):
        """
        Update the version_data dictionary to change the data for the Version
        that will be created in Shotgun.
        """
        #  CBSD Customization
        # ===========================

        preset = task._preset
        properties = preset.properties()
        file_type = properties.get("file_type", '')
        colorspace = properties.get("colourspace", '')
        # todo Account for Passthrough

        sg_version_type = self.parent.execute_hook_method("hook_resolve_custom_strings", "getVersionType", task=task)

        # Rework the Version code. Get rid of the capitalization that happens by default.
        file_name = os.path.basename(task._resolved_export_path)
        file_name = os.path.splitext(file_name)[0]

        sg_version_number = int(
            self.parent.execute_hook_method("hook_resolve_custom_strings", "getAutoVersion", task=task)
        )
        version_data.update({
            'code': file_name,
            'sg_version_number': sg_version_number,
            'sg_version_type': sg_version_type,
            'sg_file_type': file_type,
            'sg_colorspace': colorspace,
        })

        # ===========================
