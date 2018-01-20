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

#  CBSD Customization
# ===========================
import hiero.ui
import hiero.core
from TagElements import TagElementsAction
# ===========================

class HieroPreExport(Hook):
    """
    Allows clearing of caches prior to shot processing
    """
    #  CBSD Customization
    # ===========================
    _SUPPRESS_CLEAR_CACHE = False
    _IS_CLEAR_SUPPRESSION_EVENT_REGISTERED = False
    # ===========================

    def execute(self, processor, **kwargs):
        """
        Allows clearing of caches prior to shot processing. This is called just prior to export.

        :param processor: Processor The is being used, in case distinguishing between
                          differnt exports is needed.
        """

        #  CBSD Customization
        # ===========================
        # Run the TagElements tool before export to ensure that all metadata is current.
        for action in hiero.ui.registeredActions():
            if isinstance(action, TagElementsAction):
                # The suppression mode flag is needed due to Hiero's behavior when editing the Export Template
                # in the GUI dialog. Providing the flag means that the Tag Elements Action will only execute once in
                # the current GUI Context. This is beneficial in the Export Dialog because in Nuke 10.5+,
                # due to the 'preview' feature, the processor is re-instantiated every time the Export
                # Template is edited (in any way whatsoever). Since when we are editing the Export Template,
                # it does us no good to have the tool chugging away on every click which leads to an
                # irritating lagging sensation, 'suppression mode' will make it run only once,
                # until we change contexts (cancel or initiate the export)
                action.execute(enter_suppression_mode=True)
                break

        # as with the `enter_suppression_mode` in the above tool-call, lets take measures to prevent
        # the repeated querying of shotgun when the user is editing the Export Template, effectively keeping
        # that interaction snappy!
        if not self.__class__._IS_CLEAR_SUPPRESSION_EVENT_REGISTERED:
            hiero.core.events.registerInterest('kContextChanged', self.resetSuppressClearCache)
            self.__class__._IS_CLEAR_SUPPRESSION_EVENT_REGISTERED = True

        if not self.__class__._SUPPRESS_CLEAR_CACHE:
            self.parent.execute_hook_method("hook_resolve_custom_strings", "cbsd_clear_lookup_cache")
            self.__class__._SUPPRESS_CLEAR_CACHE = True

        # Reset the caches for the get shot hook.
        self.parent.execute_hook_method("hook_get_shot", "reset_custom_caches")
        # ===========================

    #  CBSD Customization
    # ===========================
    def resetSuppressClearCache(self, event):
        self.__class__._SUPPRESS_CLEAR_CACHE = False
    # ===========================
