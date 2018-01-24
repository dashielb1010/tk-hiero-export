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
from messaging import showError
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

        # Make sure we reset the cache when we are in fact beginning an export.
        if not self.__class__._SUPPRESS_CLEAR_CACHE:
            self.parent.execute_hook_method("hook_resolve_custom_strings", "cbsd_clear_lookup_cache")
            self.__class__._SUPPRESS_CLEAR_CACHE = True

        # Reset the caches for the get shot hook.
        self.parent.execute_hook_method("hook_get_shot", "reset_custom_caches")

        defaultProcessTaskPreQueue = processor.processTaskPreQueue

        def processTaskPreQueuePatch(*args, **kwargs):
            """
            Patch for the ShotgunShotProcessor.processTaskPreQueue method
            used to abort exports if certain requirements are not met.
            """
            # If required, make sure the Element Tag is present.
            if processor._preset.properties().get('requireCbsdElementTag'):
                correct_element_type = processor._preset.properties().get("correctElementType")
                try:
                    assert correct_element_type
                except:
                    msg = 'Error: Unable to get setting "correctElementType"!'
                    showError(msg)
                    raise RuntimeError(msg)

                items_no_element_tag = []
                items_wrong_element_type = []

                for taskGroup in processor._submission.children():
                    for task in taskGroup.children():
                        item = task._item

                        if not isinstance(item.parent(), hiero.core.VideoTrack):
                            # While exporting Audio Items is not fully supported in our pipeline,
                            # This might still be a gotcha let's avoid.
                            continue

                        element_tag = self.parent.execute_hook_method("hook_resolve_custom_strings",
                                                                      "getCbsdElementTag",
                                                                      item=item
                                                                      )
                        if not element_tag and item not in items_no_element_tag:
                            items_no_element_tag.append(item)
                            continue

                        element_type = self.parent.execute_hook_method("hook_resolve_custom_strings",
                                                                       "getElementTagMetadataValue",
                                                                       item=item, metadata_key='tag.element_type'
                                                                       )
                        if element_type != correct_element_type and item not in items_wrong_element_type:
                            items_wrong_element_type.append(item)

                if items_no_element_tag or items_wrong_element_type:
                    msg = "Export Aborted.\n"
                    if items_no_element_tag:
                        msg += "The following items had no Cbsd Element Tag:\n%s" \
                               % '\n  - '.join(sorted([item.name() for item in items_no_element_tag]))

                    if items_wrong_element_type:
                        msg += "The following items were not the correct element type (%s):\n%s" \
                               % (correct_element_type,
                                  '\n  - '.join(sorted([item.name() for item in items_wrong_element_type]))
                                  )

                    showError(msg)
                    raise RuntimeError(msg)

            # If required, make sure no footage is RED for a passthrough
            # The source media transforms vs the write node media transforms.

            abort_red_clips = []
            for taskGroup in processor._submission.children():

                for task in taskGroup.children():
                    item = task._item

                    if not isRedClip(item.source()):
                        continue

                    is_colorspace_passthrough = task._preset.properties().get('colorspacePassthrough')
                    is_abort_if_red_clips = task._preset.properties().get('abortIfRedClips')

                    if is_abort_if_red_clips and is_colorspace_passthrough and item not in abort_red_clips:
                        abort_red_clips.append(item)

            if abort_red_clips:
                msg = "Export Aborted.\n"
                msg += "The following items are sourced from RED footage and cannot be 'passed-through':\n\n" \
                       "  - %s\n\n" \
                       "Please omit them from the export or otherwise choose the appropriate export preset and " \
                       "color transform." \
                       % '\n  - '.join(sorted([item.name() for item in abort_red_clips]))

                showError(msg)
                raise RuntimeError(msg)

            # If all is well, proceed with the export!
            defaultProcessTaskPreQueue(*args, **kwargs)

        processor.processTaskPreQueue = processTaskPreQueuePatch

        # ===========================

    #  CBSD Customization
    # ===========================
    def resetSuppressClearCache(self, event):
        self.__class__._SUPPRESS_CLEAR_CACHE = False
    # ===========================

#  CBSD Customization
# ===========================
def isRedClip(clip):
    """
    Test for RED-ness
    """
    media_source = clip.mediaSource()
    if media_source.isOffline():
        return False
    elif media_source.metadata().dict().get("foundry.source.type", "") == 'RED R3D':
        return True
    else:
        return False
# ===========================