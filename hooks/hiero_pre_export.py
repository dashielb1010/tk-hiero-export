# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from sgtk import Hook


class HieroPreExport(Hook):
    """
    Allows clearing of caches prior to shot processing
    """
    def execute(self, processor, **kwargs):
        """
        Allows clearing of caches prior to shot processing. This is called just prior to export.

        :param processor: Processor The is being used, in case distinguishing between
                          differnt exports is needed.
        """

        #  CBSD Customization
        # ===========================
        self.parent.execute_hook_method("hook_resolve_custom_strings", "cbsd_clear_lookup_cache")

        # todo: For the custom CBSD Hiero Exporter, we are going to rely on a custom plugin to populate the GUI (cont.)...
        # with our additional options. We will use this script to evaluate if that has happened successfully, since
        # we cannot actually make those modifications from within any of the available hooks-- but they will be
        # integral to the way the hooks end up impacting the app behavior.

        # todo: if customizations are validated, patch the exporter, otherwise, show a warning dialog with the option to cancel
        # ===========================
