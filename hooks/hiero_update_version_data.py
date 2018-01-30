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
from pprint import pprint, pformat
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

        self.parent.logger.debug("Saving the item on the task for use in the post_version_creation hook.")

        # Take advantage of the fact the the `_item` attribute hasn't been deleted yet!
        # (For use in the post_version_creation hook)
        task._preserved_item = task._item

        preset = task._preset
        properties = preset.properties()
        file_type = properties.get("file_type", '')

        # Determining and act based on whether the render task is a frame sequence or a movie.
        nuke_sequence_file_types = ['avi', 'cin', 'dpx', 'exr', 'jpeg', 'pic', 'png', 'sgi', 'targa', 'tiff']
        nuke_movie_file_types = ['mov', ]

        # -- Export is a sequence
        if file_type in nuke_sequence_file_types:
            version_data['sg_path_to_frames'] = task._resolved_export_path
            if 'sg_path_to_movie' in version_data:
                del version_data['sg_path_to_movie']

        # -- Export is a movie
        elif file_type in nuke_movie_file_types:
            version_data['sg_path_to_movie'] = task._resolved_export_path
            if 'sg_path_to_frames' in version_data:
                del version_data['sg_path_to_frames']

        colorspace = properties.get("colourspace", '')

        # Determine Frame Ranges
        handles = task._cutHandles if task._cutHandles is not None else 0
        startFrame = task._startFrame or 0

        cut_in_offset = self.parent.execute_hook_method("hook_resolve_custom_strings",
                                                        "getElementTagMetadataValue",
                                                        item=task._item,
                                                        metadata_key='tag.cut_in_offset',
                                                        )
        cut_out_offset = self.parent.execute_hook_method("hook_resolve_custom_strings",
                                                         "getElementTagMetadataValue",
                                                         item=task._item,
                                                         metadata_key='tag.cut_out_offset',
                                                         )
        first_frame = int(cut_in_offset) + startFrame
        last_frame = int(cut_out_offset) + startFrame + 2*handles

        # Get the Version Type
        sg_version_type = self.parent.execute_hook_method("hook_resolve_custom_strings", "getVersionType", task=task)

        # Rework the Version's code field. Get rid of the capitalization that happens by default-- unnecessary.
        file_name = os.path.basename(task._resolved_export_path)
        file_name = os.path.splitext(file_name)[0]

        # Get the Version Number
        sg_version_number = int(
            self.parent.execute_hook_method("hook_resolve_custom_strings", "getAutoVersion", task=task)
        )

        # Get the format dimensions
        if task._preset.properties()['reformat']['to_type'] == 'None':
            width = int(task._item.source().format().width())
            height = int(task._item.source().format().height())

        elif task._preset.properties()['reformat']['to_type'] == 'To Sequence Resolution':
            width = int(task._item.parentSequence().format().width())
            height = int(task._item.parentSequence().format().height())

        elif task._preset.properties()['reformat']['to_type'] == 'scale':
            # Note that these values very likely will not be accurate if the result of the multiplication is a
            # non-integer value. If accuracy in that case is required, Nuke's reformatting behavior should be explored
            # to determine how it handles rounding of pixel dimensions when 'scaling' so that logic can be reflected
            # here, --or-- determining and populating such values should take place once the actual resulting
            # images are available and their resolution can be read instead of guessed-at.
            width = int(task._item.source().format().width() * task._preset.properties()['reformat']['scale'])
            height = int(task._item.source().format().height() * task._preset.properties()['reformat']['scale'])

        elif task._preset.properties()['reformat']['to_type'] == 'to format':
            width = int(task._preset.properties()['reformat']['width'])
            height = int(task._preset.properties()['reformat']['height'])

        else:
            width = 0
            height = 0
            self.parent.logger.warning("Export Properties have unknown reformat type: '%s'\nProperties dict:\n%s"
                                       % (task._preset.properties()['reformat']['to_type'],
                                          pformat(task._preset.properties()))
                                       )
        updated_data = {
            'code': file_name,
            'sg_version_number': sg_version_number,
            'sg_version_type': sg_version_type,
            'sg_file_type': file_type,
            'sg_colorspace': colorspace,
            'sg_task': self.parent.context.task,
            'sg_width': width,
            'sg_height': height,
            'sg_first_frame': first_frame,
            'sg_last_frame': last_frame,
            'frame_range': '-'.join([str(task._item.sourceIn()), str(task._item.sourceIn())]),
            'frame_count': int(task._item.sourceDuration()),
            # 'frame_rate':   # Todo determine frame rate ?
        }
        self.parent.logger.debug("Updated data: \n%s" % pformat(sorted(updated_data)))
        version_data.update(updated_data)

        # ===========================
